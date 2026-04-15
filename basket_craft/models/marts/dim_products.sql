{{ config(materialized='table') }}

select
    product_id,
    product_name,
    description,
    created_date as product_launch_date

from {{ ref('stg_products') }}
