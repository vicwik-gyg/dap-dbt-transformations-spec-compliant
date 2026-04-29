-- stg_seed_data__dim_date: 1:1 staging of date spine reference data.
-- Rule L01: no joins. Rule L02: view. Rule N01: stg_<source>__<entity>.

select
    cast(date_id as date) as date_id

from {{ source('seed_data', 'seed_dim_date') }}
