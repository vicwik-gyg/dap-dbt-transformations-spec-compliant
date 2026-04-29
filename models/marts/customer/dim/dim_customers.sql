{{
    config(
        materialized='table',
        unique_key='customer_id'
    )
}}

select
    customer_id,
    customer_email,
    customer_country,
    signup_source,
    is_verified,
    created_at,
    updated_at,
    datediff(current_date(), cast(created_at as date)) as days_since_signup
from {{ ref('stg_seed_data__customers') }}
