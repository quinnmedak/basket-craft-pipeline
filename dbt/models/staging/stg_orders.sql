select
    order_id::integer as order_id,
    user_id::integer as customer_id,
    website_session_id::integer as website_session_id,
    primary_product_id::integer as primary_product_id,
    items_purchased::integer as items_purchased,
    created_at as order_date,
    price_usd,
    cogs_usd
from {{ source('raw', 'orders') }}
