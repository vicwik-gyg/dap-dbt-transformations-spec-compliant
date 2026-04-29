-- stg_seed_data__bookings: 1:1 staging of raw booking records.
-- Rule L01: no joins in staging. Rule L02: materialized as view.
-- Rule N01: stg_<source>__<entity>

select
    cast(booking_id as bigint) as booking_id,
    cast(tour_id as bigint) as tour_id,
    cast(customer_id as bigint) as customer_id,
    cast(supplier_id as bigint) as supplier_id,
    cast(destination_id as bigint) as destination_id,
    cast(booking_status as string) as booking_status,
    cast(number_of_participants as int) as number_of_participants,
    cast(total_price_in_cents as bigint) as total_price_in_cents,
    cast(currency_code as string) as currency_code,
    cast(commission_rate as decimal(5, 4)) as commission_rate,
    cast(checkout_at as timestamp) as checkout_at,
    cast(travel_at as timestamp) as travel_at,
    cast(created_at as timestamp) as created_at,
    cast(cancelled_at as timestamp) as cancelled_at,
    booking_status in ('canceled', 'deleted', 'deleted_by_customer', 'deleted_by_daemon') as is_cancelled

from {{ source('seed_data', 'seed_bookings') }}
