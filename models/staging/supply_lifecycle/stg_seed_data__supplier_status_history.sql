-- stg_seed_data__supplier_status_history: 1:1 staging of supplier status changes.
-- Tracks gyg_status transitions for deactivation window detection.
-- Rule L01: no joins. Rule L02: view. Rule N01: stg_<source>__<entity>.

select
    cast(user_id as bigint) as user_id,
    cast(gyg_status as string) as gyg_status,
    cast(deactivation_reason_id as int) as deactivation_reason_id,
    cast(update_timestamp as timestamp) as update_timestamp

from {{ source('seed_data', 'seed_supplier_status_history') }}
