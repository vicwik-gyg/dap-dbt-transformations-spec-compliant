-- stg_seed_data__customers: 1:1 staging of customer account records.
-- Rule L01: no joins. Rule L02: view. Rule N01: stg_<source>__<entity>.

select
    cast(customer_id as bigint) as customer_id,
    cast(customer_email as string) as customer_email,
    cast(customer_country as string) as customer_country,
    cast(signup_source as string) as signup_source,
    cast(is_verified as boolean) as is_verified,
    cast(created_at as timestamp) as created_at,
    cast(updated_at as timestamp) as updated_at

from {{ source('seed_data', 'seed_customers') }}
