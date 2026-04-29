{{
    config(
        materialized='table',
        unique_key=['supplier_id', 'valid_from']
    )
}}

-- dim_supplier_lifecycle_stage_history: SCD Type 2 supplier lifecycle.
-- Aggregates tour-level lifecycle stages to the supplier level. Includes
-- suppliers with zero tours. Self-requested deactivations override to Churned.
--
-- Base filters (on latest state in dim_supplier):
--   - user_type = 'supplier'
--   - date_of_registration is not null
--   - company_name not like '%getyourguide%' (internal accounts)
--
-- Stages (daily, first match wins):
--   01. Created       — Registered but no tour has ever been online
--   02. Pre-Activated — At least one tour Pre-Activated (none Activated)
--   03. Activated     — At least one tour Activated
--   04. Dormant       — At least one tour Dormant (none Activated/Pre-Activated)
--   05. Churned       — Self-deactivation window OR all tours Churned/vanished

with

date_spine as (
    select date_id as date
    from {{ ref('stg_seed_data__dim_date') }}
),

-- Base supplier universe: latest-state filter.
supplier_base as (
    select
        user_id as supplier_id,
        cast(date_of_registration as date) as registration_date
    from {{ ref('stg_seed_data__supplier_dim') }}
    where user_type = 'supplier'
        and date_of_registration is not null
        and lower(coalesce(company_name, '')) not like '%getyourguide%'
),

-- Self-requested deactivation events (reason_id in 1, 3, 5, 6, 16).
self_deactivation_events as (
    select
        user_id as supplier_id,
        cast(update_timestamp as date) as deactivated_from
    from {{ ref('stg_seed_data__supplier_status_history') }}
    where gyg_status = 'deactivated'
        and deactivation_reason_id in (1, 3, 5, 6, 16)
),

-- Reactivation events.
reactivation_events as (
    select
        user_id as supplier_id,
        cast(update_timestamp as date) as reactivated_at
    from {{ ref('stg_seed_data__supplier_status_history') }}
    where gyg_status = 'active'
),

-- Build deactivation windows: from deactivation to next reactivation.
self_deactivation_windows as (
    select
        d.supplier_id,
        d.deactivated_from,
        coalesce(
            min(r.reactivated_at),
            date_add(current_date(), 1)
        ) as deactivated_to
    from self_deactivation_events as d
    left join reactivation_events as r
        on d.supplier_id = r.supplier_id
        and r.reactivated_at > d.deactivated_from
    group by d.supplier_id, d.deactivated_from
),

-- Daily spine per supplier from registration to end of date spine.
supplier_daily_spine as (
    select
        b.supplier_id,
        d.date
    from supplier_base as b
    inner join date_spine as d
        on d.date >= b.registration_date
),

-- Tour-level stages expanded to daily grain.
tour_stages_daily as (
    select
        d.date,
        t.tour_id,
        t.supplier_id,
        t.lifecycle_stage,
        t.is_ever_activated
    from {{ ref('dim_tour_lifecycle_stage_history') }} as t
    inner join date_spine as d
        on d.date between t.valid_from and t.valid_to
),

-- Aggregate tour stages to supplier/day level.
supplier_tour_agg as (
    select
        date,
        supplier_id,
        case
            when count_if(lifecycle_stage = '03. Activated') > 0 then '03. Activated'
            when count_if(lifecycle_stage = '02. Pre-Activated') > 0 then '02. Pre-Activated'
            when count_if(lifecycle_stage = '04. Dormant') > 0 then '04. Dormant'
            when count_if(lifecycle_stage = '05. Churned') > 0 then '05. Churned'
            else '01. Created'
        end as lifecycle_stage,
        max(cast(is_ever_activated as int)) = 1 as is_ever_activated
    from tour_stages_daily
    group by date, supplier_id
),

-- Join spine with tour aggregates; force Churned in self-deactivation windows.
supplier_stage_daily as (
    select
        s.date,
        s.supplier_id,
        case
            when w.supplier_id is not null then '05. Churned'
            else coalesce(a.lifecycle_stage, '01. Created')
        end as lifecycle_stage,
        coalesce(a.is_ever_activated, false) as is_ever_activated,
        w.supplier_id is not null as is_self_deactivated
    from supplier_daily_spine as s
    left join supplier_tour_agg as a
        on s.supplier_id = a.supplier_id
        and s.date = a.date
    left join self_deactivation_windows as w
        on s.supplier_id = w.supplier_id
        and s.date >= w.deactivated_from
        and s.date < w.deactivated_to
),

-- Prevent regression to Created: once a supplier has been non-Created,
-- losing all tours forces Churned rather than going back to Created.
with_stage_floor as (
    select
        *,
        max(case when lifecycle_stage != '01. Created' then 1 else 0 end) over (
            partition by supplier_id
            order by date
            rows between unbounded preceding and current row
        ) as has_ever_been_non_created,
        max(cast(is_ever_activated as int)) over (
            partition by supplier_id
            order by date
            rows between unbounded preceding and current row
        ) = 1 as is_ever_activated_sticky
    from supplier_stage_daily
),

with_corrected_stage as (
    select
        date,
        supplier_id,
        case
            when lifecycle_stage = '01. Created' and has_ever_been_non_created = 1
            then '05. Churned'
            else lifecycle_stage
        end as lifecycle_stage,
        is_ever_activated_sticky as is_ever_activated,
        is_self_deactivated,
        lifecycle_stage = '01. Created'
            and has_ever_been_non_created = 1
            and not is_self_deactivated
            as is_tours_vanished
    from with_stage_floor
),

-- Detect stage changes. New runs also start on deactivation/vanish flag changes.
with_change_flag as (
    select
        *,
        case
            when lifecycle_stage != lag(lifecycle_stage) over (
                partition by supplier_id order by date
            )
            or is_self_deactivated != lag(is_self_deactivated) over (
                partition by supplier_id order by date
            )
            or is_tours_vanished != lag(is_tours_vanished) over (
                partition by supplier_id order by date
            )
            or lag(lifecycle_stage) over (partition by supplier_id order by date) is null
            then 1
            else 0
        end as is_stage_change
    from with_corrected_stage
),

-- Group consecutive same-stage days into runs.
with_stage_run as (
    select
        *,
        sum(is_stage_change) over (
            partition by supplier_id
            order by date
            rows between unbounded preceding and current row
        ) as stage_run_id
    from with_change_flag
),

-- Collapse each run into a single SCD2 row.
collapsed as (
    select
        supplier_id,
        lifecycle_stage,
        min(date) as valid_from,
        max(date) as valid_to,
        datediff(max(date), min(date)) + 1 as days_in_stage,
        max(cast(is_ever_activated as int)) = 1 as is_ever_activated,
        max(cast(is_self_deactivated as int)) = 1 as is_self_deactivated,
        max(cast(is_tours_vanished as int)) = 1 as is_tours_vanished,
        stage_run_id
    from with_stage_run
    group by supplier_id, lifecycle_stage, stage_run_id
)

select
    supplier_id,
    lifecycle_stage,
    valid_from,
    valid_to,
    valid_to = max(valid_to) over (partition by supplier_id) as is_current,
    days_in_stage,
    is_ever_activated,
    is_self_deactivated,
    is_tours_vanished,
    lag(lifecycle_stage) over (
        partition by supplier_id order by stage_run_id
    ) as previous_stage,
    stage_run_id
from collapsed
