-- stg_seed_data__reviews: 1:1 staging of tour review records.
-- Rule L01: no joins. Rule L02: view. Rule N01: stg_<source>__<entity>.

select
    cast(review_id as bigint) as review_id,
    cast(activity_id as bigint) as activity_id,
    cast(status as string) as status,
    cast(created_at as timestamp) as created_at,
    cast(date as date) as date

from {{ source('seed_data', 'seed_reviews') }}
