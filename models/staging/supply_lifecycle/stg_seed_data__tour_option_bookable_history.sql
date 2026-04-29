-- stg_seed_data__tour_option_bookable_history: 1:1 staging of bookable status CDC.
-- Each row is a change-data-capture event for tour option bookability.
-- Rule L01: no joins. Rule L02: view. Rule N01: stg_<source>__<entity>.

select
    cast(tour_id as bigint) as tour_id,
    cast(tour_option_id as bigint) as tour_option_id,
    cast(binlog_timestamp as timestamp) as binlog_timestamp,
    cast(bookable_status as boolean) as bookable_status,
    cast(supplier_status as string) as supplier_status,
    cast(tour_status as string) as tour_status,
    cast(tour_option_status as string) as tour_option_status

from {{ source('seed_data', 'seed_tour_option_bookable_history') }}
