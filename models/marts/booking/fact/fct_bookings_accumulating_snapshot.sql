{{
    config(
        materialized='table',
        unique_key='booking_id'
    )
}}

with
bookings as (select * from {{ ref('int_bookings_enriched') }}),
milestones as (select * from {{ ref('int_bookings_with_milestones') }})

select
    b.booking_id, b.tour_id, b.customer_id, b.supplier_id, b.destination_id,
    b.number_of_participants, b.total_price_in_cents, b.currency_code,
    m.pending_at, m.confirmed_at, m.cancellation_requested_at,
    m.cancelled_at, m.cancelled_by,
    m.is_confirmed, m.is_cancelled,
    m.seconds_pending_to_confirmed, m.seconds_request_to_cancellation,
    case
        when m.cancelled_at is not null then 'cancelled'
        when m.cancellation_requested_at is not null then 'cancellation_requested'
        when m.confirmed_at is not null then 'confirmed'
        when m.pending_at is not null then 'pending'
        else 'unknown'
    end as current_lifecycle_stage
from bookings as b
left join milestones as m on b.booking_id = m.booking_id
