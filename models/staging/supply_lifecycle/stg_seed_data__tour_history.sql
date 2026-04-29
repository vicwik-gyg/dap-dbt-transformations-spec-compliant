-- stg_seed_data__tour_history: 1:1 staging of tour SCD2 history.
-- Each row captures a state change for a tour's is_online flag.
-- Rule L01: no joins. Rule L02: view. Rule N01: stg_<source>__<entity>.

select
    cast(tour_id as bigint) as tour_id,
    cast(user_id as bigint) as user_id,
    cast(is_online as boolean) as is_online,
    cast(update_timestamp_org as timestamp) as update_timestamp_org

from {{ source('seed_data', 'seed_tour_history') }}
