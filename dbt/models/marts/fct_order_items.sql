{{ config(materialized='table') }}

select
    oi.order_item_id,
    oi.order_id,
    o.customer_id,
    oi.product_id,
    o.order_date,
    oi.is_primary_item,
    1                               as quantity,
    oi.price_usd                    as unit_price,
    oi.price_usd                    as line_total,
    oi.cogs_usd

from {{ ref('stg_order_items') }} oi
left join {{ ref('stg_orders') }} o
    on oi.order_id = o.order_id
