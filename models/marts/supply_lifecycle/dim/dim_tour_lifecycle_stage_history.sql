{{
    config(
        materialized='table',
        unique_key=['tour_id', 'supplier_id', 'valid_from']
    )
}}

-- dim_tour_lifecycle_stage_history: SCD Type 2 tour lifecycle.
-- One row per stage run per tour/supplier pair. Stages evaluated daily:
--   01. Created       — Tour has never been online
--   02. Pre-Activated — Online within last 90 days but < 3 active reviews
--   03. Activated     — 3+ active reviews AND online within last 90 days
--   04. Dormant       — No online day in the last 90 days (but < 365)
--   05. Churned       — No online day in the last 365 days

with

-- Date of the 3rd active review per tour (activation threshold).
tour_activation as (
    select
        activity_id as tour_id,
        date as activation_date
    from {{ ref('stg_seed_data__reviews') }}
    where status = 'active'
    qualify row_number() over (partition by activity_id order by created_at asc) = 3
),

-- Enrich daily online status with running metrics.
enriched as (
    select
        t.date,
        t.tour_id,
        t.supplier_id,
        t.is_online,
        max(cast(t.is_online as int)) over (
            partition by t.tour_id
            order by t.date
            rows between unbounded preceding and current row
        ) = 1 as has_ever_been_online,
        max(case when t.is_online then t.date end) over (
            partition by t.tour_id
            order by t.date
            rows between unbounded preceding and current row
        ) as last_online_date,
        case
            when a.activation_date is not null and t.date >= a.activation_date
            then true
            else false
        end as is_ever_activated,
        a.activation_date
    from {{ ref('int_tour_online_daily') }} as t
    left join tour_activation as a on t.tour_id = a.tour_id
),

-- Assign lifecycle stage per day (first matching rule wins).
staged as (
    select
        date,
        tour_id,
        supplier_id,
        is_ever_activated,
        activation_date,
        case
            when not has_ever_been_online then '01. Created'
            when datediff(date, last_online_date) >= 365 then '05. Churned'
            when datediff(date, last_online_date) >= 90 then '04. Dormant'
            when is_ever_activated then '03. Activated'
            else '02. Pre-Activated'
        end as lifecycle_stage
    from enriched
),

-- Detect stage transitions per tour/supplier pair.
with_change_flag as (
    select
        *,
        case
            when lifecycle_stage != lag(lifecycle_stage) over (
                partition by tour_id, supplier_id order by date
            )
            or lag(lifecycle_stage) over (
                partition by tour_id, supplier_id order by date
            ) is null
            then 1
            else 0
        end as is_stage_change
    from staged
),

-- Group consecutive same-stage days into runs.
with_stage_run as (
    select
        *,
        sum(is_stage_change) over (
            partition by tour_id, supplier_id
            order by date
            rows between unbounded preceding and current row
        ) as stage_run_id
    from with_change_flag
),

-- Collapse each run into a single SCD2 row.
collapsed as (
    select
        tour_id,
        supplier_id,
        lifecycle_stage,
        min(date) as valid_from,
        max(date) as valid_to,
        datediff(max(date), min(date)) + 1 as days_in_stage,
        max(cast(is_ever_activated as int)) = 1 as is_ever_activated,
        max(activation_date) as activation_date,
        stage_run_id
    from with_stage_run
    group by tour_id, supplier_id, lifecycle_stage, stage_run_id
)

select
    tour_id,
    supplier_id,
    lifecycle_stage,
    valid_from,
    valid_to,
    valid_to = max(valid_to) over (partition by tour_id) as is_current,
    days_in_stage,
    is_ever_activated,
    activation_date,
    lag(lifecycle_stage) over (
        partition by tour_id, supplier_id order by stage_run_id
    ) as previous_stage,
    stage_run_id
from collapsed
