-- stg_seed_data__booking_status_changes: 1:1 staging of booking status events.
-- Simulates a Kafka topic of booking lifecycle events.
-- Rule L01: no joins. Rule L02: view. Rule N01: stg_<source>__<entity>.

select
    cast(booking_id as bigint) as booking_id,
    cast(booking_status as string) as booking_status,
    cast(changed_at as timestamp) as changed_at,
    cast(changed_by as string) as changed_by

from {{ source('seed_data', 'seed_booking_status_history') }}
