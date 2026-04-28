{{
    config(
        materialized='table',
        unique_key='booking_id'
    )
}}

select
    booking_id, tour_id, customer_id, supplier_id, destination_id,
    booking_status, is_cancelled, number_of_participants,
    total_price_in_cents, currency_code, commission_rate,
    commission_in_cents, supplier_payout_in_cents,
    checkout_at, travel_at, created_at, cancelled_at,
    tour_name, tour_category, tour_list_price_in_cents, tour_duration_minutes,
    destination_name, destination_city, destination_country, destination_continent,
    cast(checkout_at as date) as checkout_date,
    cast(travel_at as date) as travel_date
from {{ ref('int_bookings_enriched') }}
