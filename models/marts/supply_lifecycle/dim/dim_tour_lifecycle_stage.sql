-- dim_tour_lifecycle_stage: latest lifecycle stage per tour/supplier pair.
-- Current-state view on top of the SCD2 history table.

select
    tour_id,
    supplier_id,
    lifecycle_stage,
    valid_from as stage_start_date,
    days_in_stage,
    previous_stage,
    is_ever_activated,
    activation_date
from {{ ref('dim_tour_lifecycle_stage_history') }}
where is_current = true
