-- int_tour_online_daily: compute daily online status per tour.
-- Combines two sources (bookable history + tour history) to determine
-- whether a tour was online on any given day. A tour is online if EITHER
-- source indicates it was active at any point during that day.
-- Rule N02: int_<entity>_<verb>

with

date_spine as (
    select date_id as date
    from {{ ref('stg_seed_data__dim_date') }}
),

-- Source 1: bookable_history (tour-option level, aggregated to tour level).
-- A tour is online when ANY option has bookable_status = true and all
-- parent statuses (supplier, tour, tour_option) are active.
bookable_changes as (
    select
        tour_id,
        tour_option_id,
        binlog_timestamp as change_timestamp,
        bookable_status,
        (
            supplier_status = 'active'
            and tour_status = 'active'
            and tour_option_status = 'active'
        ) as all_statuses_active
    from {{ ref('stg_seed_data__tour_option_bookable_history') }}
),

-- Build validity periods per tour_option, keeping only online periods.
bookable_option_periods as (
    select
        tour_id,
        tour_option_id,
        change_timestamp as period_start,
        coalesce(
            lead(change_timestamp) over (
                partition by tour_option_id
                order by change_timestamp
            ),
            current_timestamp()
        ) as period_end
    from bookable_changes
    where bookable_status = true and all_statuses_active = true
),

-- Expand to daily grain per tour_option.
bookable_option_daily as (
    select
        d.date,
        p.tour_id,
        p.tour_option_id
    from date_spine as d
    inner join bookable_option_periods as p
        on d.date between cast(p.period_start as date) and cast(p.period_end as date)
),

-- Aggregate to tour level: tour is online if ANY option is online.
bookable_daily as (
    select
        date,
        tour_id,
        true as is_online_bookable
    from bookable_option_daily
    group by date, tour_id
),

-- Source 2: dim_tour_history (tour level SCD).
dim_tour_periods as (
    select
        tour_id,
        user_id as supplier_id,
        is_online,
        update_timestamp_org as period_start,
        coalesce(
            lead(update_timestamp_org) over (
                partition by tour_id order by update_timestamp_org
            ),
            current_timestamp()
        ) as period_end
    from {{ ref('stg_seed_data__tour_history') }}
),

-- Expand to daily grain. max(is_online) ensures a day counts as online
-- if the tour was online at any point during that day.
dim_tour_daily as (
    select
        d.date,
        p.tour_id,
        p.supplier_id,
        max(cast(p.is_online as int)) as is_online_dim_tour
    from date_spine as d
    inner join dim_tour_periods as p
        on d.date between cast(p.period_start as date) and cast(p.period_end as date)
    group by d.date, p.tour_id, p.supplier_id
)

-- Combine both sources: a tour is online if either source says so.
select
    dt.date,
    dt.tour_id,
    dt.supplier_id,
    coalesce(b.is_online_bookable, false)
        or coalesce(cast(dt.is_online_dim_tour as boolean), false) as is_online
from dim_tour_daily as dt
left join bookable_daily as b
    on dt.tour_id = b.tour_id
    and dt.date = b.date
