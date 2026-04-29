{{
    config(
        materialized='table',
        unique_key=['supplier_id', 'version_number']
    )
}}

with
source_versions as (select * from {{ ref('stg_seed_data__supplier_versions') }}),
numbered as (
    select
        supplier_id, supplier_name, supplier_email, destination_id,
        is_verified, is_active, valid_from, valid_to, operation,
        valid_to is not null and valid_to = timestamp('9999-12-31 23:59:59') as is_current_version,
        row_number() over (partition by supplier_id order by valid_from nulls first) as version_number
    from source_versions
),
versioned as (
    select
        {{ dbt_utils.generate_surrogate_key(['supplier_id', 'version_number']) }} as supplier_version_id,
        supplier_id, supplier_name, supplier_email, destination_id,
        is_verified, is_active, valid_from, valid_to, operation,
        is_current_version, version_number
    from numbered
)
select * from versioned
