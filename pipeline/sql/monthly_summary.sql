TRUNCATE analytics.monthly_sales_by_product;

INSERT INTO analytics.monthly_sales_by_product
    (month, product_name, gross_revenue, order_count, avg_order_value, etl_loaded_at)
SELECT
    DATE_TRUNC('month', oi.created_at)::DATE   AS month,
    p.product_name,
    SUM(oi.price_usd)                          AS gross_revenue,
    COUNT(DISTINCT oi.order_id)                AS order_count,
    SUM(oi.price_usd) / COUNT(DISTINCT oi.order_id) AS avg_order_value,
    NOW()                                      AS etl_loaded_at
FROM raw.order_items oi
JOIN raw.products p ON oi.product_id = p.product_id
GROUP BY 1, 2
ORDER BY 1, 2;
