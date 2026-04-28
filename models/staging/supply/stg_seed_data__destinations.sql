-- stg_seed_data__destinations: 1:1 staging of destination reference data.
-- Rule L01: no joins. Rule L02: view. Rule N01: stg_<source>__<entity>.

select
    cast(destination_id as bigint) as destination_id,
    cast(destination_name as string) as destination_name,
    cast(destination_city as string) as destination_city,
    cast(destination_country as string) as destination_country,
    cast(destination_continent as string) as destination_continent,
    cast(is_active as boolean) as is_active,
    cast(created_at as timestamp) as created_at,
    cast(updated_at as timestamp) as updated_at

from {{ source('seed_data', 'seed_destinations') }}
