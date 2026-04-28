-- Validates agg_bookings_checkout_daily: confirmed bookings in agg must match fact.

with
agg_total as (
    select sum(confirmed_bookings) as agg_confirmed
    from {{ ref('agg_bookings_checkout_daily') }}
),
fact_total as (
    select count(*) as fact_confirmed
    from {{ ref('fct_bookings') }}
    where not is_cancelled
)
select agg_confirmed, fact_confirmed
from agg_total cross join fact_total
where agg_confirmed != fact_confirmed
