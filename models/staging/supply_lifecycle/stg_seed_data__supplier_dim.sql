-- stg_seed_data__supplier_dim: 1:1 staging of supplier dimension (latest state).
-- Contains supplier metadata needed for lifecycle stage computation.
-- Rule L01: no joins. Rule L02: view. Rule N01: stg_<source>__<entity>.

select
    cast(user_id as bigint) as user_id,
    cast(user_type as string) as user_type,
    cast(company_name as string) as company_name,
    cast(date_of_registration as timestamp) as date_of_registration,
    cast(gyg_status as string) as gyg_status

from {{ source('seed_data', 'seed_supplier_dim') }}
