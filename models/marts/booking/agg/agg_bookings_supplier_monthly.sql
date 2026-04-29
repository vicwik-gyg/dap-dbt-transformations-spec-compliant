select
    date_trunc('month', checkout_date) as checkout_month,
    supplier_id,
    count(booking_id) as total_bookings,
    count(case when not is_cancelled then booking_id end) as confirmed_bookings,
    count(case when is_cancelled then booking_id end) as cancelled_bookings,
    sum(number_of_participants) as total_participants,
    sum(total_price_in_cents) as gross_bookings_in_cents,
    sum(case when not is_cancelled then total_price_in_cents else 0 end) as net_bookings_in_cents,
    sum(commission_in_cents) as total_commission_in_cents,
    sum(supplier_payout_in_cents) as total_supplier_payout_in_cents
from {{ ref('fct_bookings') }}
group by date_trunc('month', checkout_date), supplier_id
