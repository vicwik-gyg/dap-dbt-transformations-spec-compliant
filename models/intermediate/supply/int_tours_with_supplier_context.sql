-- int_tours_with_supplier_context: enriches tours with supplier and destination data.
-- Rule N02: int_<entity>_<verb>

with

tours as (
    select * from {{ ref('stg_seed_data__tours') }}
),

suppliers as (
    select * from {{ ref('stg_seed_data__suppliers') }}
),

destinations as (
    select * from {{ ref('stg_seed_data__destinations') }}
)

select
    t.tour_id,
    t.tour_name,
    t.supplier_id,
    t.destination_id,
    t.tour_category,
    t.price_in_cents,
    t.currency_code,
    t.duration_minutes,
    t.is_active as is_tour_active,
    t.created_at as tour_created_at,
    t.updated_at as tour_updated_at,

    -- supplier context
    s.supplier_name,
    s.is_verified as is_supplier_verified,
    s.is_active as is_supplier_active,

    -- destination context
    d.destination_name,
    d.destination_country,
    d.destination_continent,
    d.is_active as is_destination_active

from tours as t
left join suppliers as s
    on t.supplier_id = s.supplier_id
left join destinations as d
    on t.destination_id = d.destination_id
