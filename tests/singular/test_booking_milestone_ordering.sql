-- Validates fct_bookings_accumulating_snapshot: confirmed_at >= pending_at.

select booking_id, pending_at, confirmed_at
from {{ ref('fct_bookings_accumulating_snapshot') }}
where confirmed_at is not null
  and pending_at is not null
  and confirmed_at < pending_at
