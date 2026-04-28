select
    tour_id, tour_name, supplier_id, destination_id,
    tour_category, price_in_cents, currency_code, duration_minutes,
    is_tour_active, tour_created_at, tour_updated_at,
    supplier_name, is_supplier_verified, is_supplier_active,
    destination_name, destination_country, destination_continent
from {{ ref('int_tours_with_supplier_context') }}
