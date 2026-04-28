-- stg_seed_data__suppliers: 1:1 staging of supplier account data.
-- Rule L01: no joins. Rule L02: view. Rule N01: stg_<source>__<entity>.

select
    cast(supplier_id as bigint) as supplier_id,
    cast(supplier_name as string) as supplier_name,
    cast(supplier_email as string) as supplier_email,
    cast(destination_id as bigint) as destination_id,
    cast(is_verified as boolean) as is_verified,
    cast(is_active as boolean) as is_active,
    cast(created_at as timestamp) as created_at,
    cast(updated_at as timestamp) as updated_at

from {{ source('seed_data', 'seed_suppliers') }}
