-- stg_seed_data__tours: 1:1 staging of tour/activity catalog.
-- Rule L01: no joins. Rule L02: view. Rule N01: stg_<source>__<entity>.

select
    cast(tour_id as bigint) as tour_id,
    cast(tour_name as string) as tour_name,
    cast(supplier_id as bigint) as supplier_id,
    cast(destination_id as bigint) as destination_id,
    cast(tour_category as string) as tour_category,
    cast(price_in_cents as bigint) as price_in_cents,
    cast(currency_code as string) as currency_code,
    cast(duration_minutes as int) as duration_minutes,
    cast(is_active as boolean) as is_active,
    cast(created_at as timestamp) as created_at,
    cast(updated_at as timestamp) as updated_at

from {{ source('seed_data', 'seed_tours') }}
