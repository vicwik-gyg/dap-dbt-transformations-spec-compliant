-- stg_seed_data__suppliers: staged supplier account data, deduplicated to one row per supplier.
-- Source has multiple rows per supplier_id (one per destination). We keep the first
-- destination_id alphabetically for determinism.
-- Rule L01: no joins. Rule L02: view. Rule N01: stg_<source>__<entity>.

with ranked as (
    select
        cast(supplier_id as bigint) as supplier_id,
        cast(supplier_name as string) as supplier_name,
        cast(supplier_email as string) as supplier_email,
        cast(destination_id as bigint) as destination_id,
        cast(is_verified as boolean) as is_verified,
        cast(is_active as boolean) as is_active,
        cast(created_at as timestamp) as created_at,
        cast(updated_at as timestamp) as updated_at,
        row_number() over (
            partition by supplier_id
            order by destination_id
        ) as rn
    from {{ source('seed_data', 'seed_suppliers') }}
)

select
    supplier_id,
    supplier_name,
    supplier_email,
    destination_id,
    is_verified,
    is_active,
    created_at,
    updated_at
from ranked
where rn = 1
