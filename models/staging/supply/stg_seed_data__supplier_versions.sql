-- stg_seed_data__supplier_versions: 1:1 staging of SCD2 supplier history.
-- Each row is one version of a supplier with valid_from/valid_to window.
-- Rule L01: no joins. Rule L02: view. Rule N01: stg_<source>__<entity>.

select
    cast(supplier_id as bigint) as supplier_id,
    cast(supplier_name as string) as supplier_name,
    cast(supplier_email as string) as supplier_email,
    cast(destination_id as bigint) as destination_id,
    cast(is_verified as boolean) as is_verified,
    cast(is_active as boolean) as is_active,
    cast(valid_from as timestamp) as valid_from,
    cast(valid_to as timestamp) as valid_to,
    cast(operation as string) as operation

from {{ source('seed_data', 'seed_supplier_history') }}
