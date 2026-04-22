select
    order_item_refund_id::integer as order_item_refund_id,
    order_item_id::integer as order_item_id,
    refund_amount_usd,
    created_at as refund_date
from {{ source('raw', 'order_item_refunds') }}
