select
    order_item_id::integer as order_item_id,
    order_id::integer as order_id,
    product_id::integer as product_id,
    is_primary_item::boolean as is_primary_item,
    created_at as order_item_date,
    price_usd,
    cogs_usd
from {{ source('raw', 'order_items') }}
