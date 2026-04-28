select
    destination_id, destination_name, destination_city,
    destination_country, destination_continent,
    is_active, created_at, updated_at
from {{ ref('stg_seed_data__destinations') }}
