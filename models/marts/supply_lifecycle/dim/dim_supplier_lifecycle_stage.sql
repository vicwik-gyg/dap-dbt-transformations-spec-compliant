-- dim_supplier_lifecycle_stage: latest lifecycle stage per supplier.
-- Current-state view on top of the SCD2 history table.

select
    supplier_id,
    lifecycle_stage,
    valid_from as stage_start_date,
    days_in_stage,
    previous_stage,
    is_ever_activated,
    is_self_deactivated,
    is_tours_vanished
from {{ ref('dim_supplier_lifecycle_stage_history') }}
where is_current = true
