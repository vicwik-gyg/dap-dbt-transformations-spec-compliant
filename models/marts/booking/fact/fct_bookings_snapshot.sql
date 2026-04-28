select
    current_timestamp() as snapshot_at,
    cast(current_date() as date) as snapshot_date,
    booking_id, tour_id, customer_id, supplier_id, destination_id,
    booking_status, number_of_participants,
    total_price_in_cents, currency_code, commission_rate,
    commission_in_cents, supplier_payout_in_cents,
    checkout_at, travel_at, created_at,
    destination_name, destination_country
from {{ ref('fct_bookings') }}
where booking_status = 'confirmed'
