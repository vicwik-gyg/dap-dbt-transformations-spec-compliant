-- int_bookings_with_milestones: pivots status change events into milestone columns.
-- Used to build the accumulating snapshot (fct_bookings_accumulating_snapshot).
-- Rule N02: int_<entity>_<verb>

with

status_changes as (
    select * from {{ ref('stg_seed_data__booking_status_changes') }}
),

pivoted as (
    select
        booking_id,
        min(case when booking_status = 'pending' then changed_at end) as pending_at,
        min(case when booking_status = 'confirmed' then changed_at end) as confirmed_at,
        min(case when booking_status = 'cancellation_requested' then changed_at end) as cancellation_requested_at,
        min(case when booking_status = 'cancelled' then changed_at end) as cancelled_at,

        -- who cancelled?
        max(case when booking_status = 'cancelled' then changed_by end) as cancelled_by

    from status_changes
    group by booking_id
)

select
    booking_id,
    pending_at,
    confirmed_at,
    cancellation_requested_at,
    cancelled_at,
    cancelled_by,

    -- derived milestone flags
    confirmed_at is not null as is_confirmed,
    cancelled_at is not null as is_cancelled,

    -- time between milestones (seconds)
    case
        when confirmed_at is not null and pending_at is not null
        then unix_timestamp(confirmed_at) - unix_timestamp(pending_at)
    end as seconds_pending_to_confirmed,

    case
        when cancelled_at is not null and cancellation_requested_at is not null
        then unix_timestamp(cancelled_at) - unix_timestamp(cancellation_requested_at)
    end as seconds_request_to_cancellation

from pivoted
