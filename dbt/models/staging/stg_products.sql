select
    product_id::integer as product_id,
    product_name,
    description,
    created_at as created_date
from {{ source('raw', 'products') }}
