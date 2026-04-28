-- int_bookings_enriched: enriches bookings with tour and destination context.
-- Rule N02: int_<entity>_<verb>

with

bookings as (
    select * from {{ ref('stg_seed_data__bookings') }}
),

tours as (
    select * from {{ ref('stg_seed_data__tours') }}
),

destinations as (
    select * from {{ ref('stg_seed_data__destinations') }}
)

select
    b.booking_id,
    b.tour_id,
    b.customer_id,
    b.supplier_id,
    b.destination_id,
    b.booking_status,
    b.is_cancelled,
    b.number_of_participants,
    b.total_price_in_cents,
    b.currency_code,
    b.commission_rate,
    b.checkout_at,
    b.travel_at,
    b.created_at,
    b.cancelled_at,

    -- tour context
    t.tour_name,
    t.tour_category,
    t.price_in_cents as tour_list_price_in_cents,
    t.duration_minutes as tour_duration_minutes,

    -- destination context
    d.destination_name,
    d.destination_city,
    d.destination_country,
    d.destination_continent,

    -- derived: commission and net revenue in cents
    cast(b.total_price_in_cents * b.commission_rate as bigint) as commission_in_cents,
    cast(b.total_price_in_cents * (1 - b.commission_rate) as bigint) as supplier_payout_in_cents

from bookings as b
left join tours as t
    on b.tour_id = t.tour_id
left join destinations as d
    on b.destination_id = d.destination_id
