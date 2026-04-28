-- stg_seed_data__care_tickets: 1:1 staging of customer care ticket records.
-- Rule L01: no joins. Rule L02: view. Rule N01: stg_<source>__<entity>.

select
    cast(ticket_id as bigint) as ticket_id,
    cast(booking_id as bigint) as booking_id,
    cast(customer_id as bigint) as customer_id,
    cast(ticket_category as string) as ticket_category,
    cast(ticket_priority as string) as ticket_priority,
    cast(ticket_status as string) as ticket_status,
    cast(created_at as timestamp) as created_at,
    cast(first_response_at as timestamp) as first_response_at,
    cast(resolved_at as timestamp) as resolved_at

from {{ source('seed_data', 'seed_care_tickets') }}
