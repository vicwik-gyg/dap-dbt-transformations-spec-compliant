{{
    config(
        materialized='table',
        unique_key='review_id'
    )
}}

with

reviews as (
    select * from {{ ref('stg_seed_data__reviews') }}
),

tours as (
    select * from {{ ref('stg_seed_data__tours') }}
)

select
    r.review_id,
    r.activity_id as tour_id,
    r.status as review_status,
    r.status = 'active' as is_active,
    r.created_at,
    r.date as review_date,

    -- tour context
    t.tour_name,
    t.supplier_id,
    t.destination_id

from reviews as r
left join tours as t
    on r.activity_id = t.tour_id
