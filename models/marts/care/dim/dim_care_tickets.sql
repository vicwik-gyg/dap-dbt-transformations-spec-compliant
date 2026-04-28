select
    ticket_id, booking_id, customer_id,
    ticket_category, ticket_priority, ticket_status,
    created_at, first_response_at, resolved_at,
    case when first_response_at is not null
        then unix_timestamp(first_response_at) - unix_timestamp(created_at)
    end as first_response_seconds,
    case when resolved_at is not null
        then unix_timestamp(resolved_at) - unix_timestamp(created_at)
    end as resolution_seconds,
    ticket_status = 'resolved' as is_resolved
from {{ ref('stg_seed_data__care_tickets') }}
