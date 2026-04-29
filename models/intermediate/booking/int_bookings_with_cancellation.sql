-- int_bookings_with_cancellation: enriches bookings with cancellation timing metrics.
-- Rule N02: int_<entity>_<verb>

with

bookings as (
    select * from {{ ref('stg_seed_data__bookings') }}
),

status_changes as (
    select * from {{ ref('stg_seed_data__booking_status_changes') }}
),

cancellations as (
    select
        booking_id,
        min(changed_at) as first_cancelled_at
    from status_changes
    where booking_status = 'cancelled'
    group by booking_id
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
    b.checkout_at,
    b.travel_at,
    b.created_at,

    -- cancellation context
    c.first_cancelled_at,
    case
        when c.first_cancelled_at is not null
        then unix_timestamp(c.first_cancelled_at) - unix_timestamp(b.created_at)
    end as seconds_to_cancellation,
    case
        when c.first_cancelled_at is not null and b.travel_at is not null
        then datediff(cast(b.travel_at as date), cast(c.first_cancelled_at as date))
    end as days_before_travel_cancelled

from bookings as b
left join cancellations as c
    on b.booking_id = c.booking_id
