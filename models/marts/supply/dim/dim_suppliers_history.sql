{{
    config(
        materialized='table',
        unique_key=['supplier_id', 'valid_from']
    )
}}

with
source_versions as (select * from {{ ref('stg_seed_data__supplier_versions') }}),
versioned as (
    select
        {{ dbt_utils.generate_surrogate_key(['supplier_id', 'valid_from']) }} as supplier_version_id,
        supplier_id, supplier_name, supplier_email, destination_id,
        is_verified, is_active, valid_from, valid_to, operation,
        valid_to = timestamp('9999-12-31 23:59:59') as is_current_version,
        row_number() over (partition by supplier_id order by valid_from) as version_number
    from source_versions
)
select * from versioned
