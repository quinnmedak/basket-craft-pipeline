-- Raw schema
CREATE SCHEMA IF NOT EXISTS raw;

CREATE TABLE IF NOT EXISTS raw.orders (
    order_id          INTEGER,
    created_at        TIMESTAMP,
    user_id           INTEGER,
    primary_product_id INTEGER,
    items_purchased   SMALLINT,
    price_usd         NUMERIC(6,2),
    cogs_usd          NUMERIC(6,2)
);

CREATE TABLE IF NOT EXISTS raw.order_items (
    order_item_id     INTEGER,
    created_at        TIMESTAMP,
    order_id          INTEGER,
    product_id        INTEGER,
    is_primary_item   SMALLINT,
    price_usd         NUMERIC(6,2),
    cogs_usd          NUMERIC(6,2)
);

CREATE TABLE IF NOT EXISTS raw.products (
    product_id        INTEGER,
    created_at        TIMESTAMP,
    product_name      VARCHAR(50),
    description       TEXT
);

-- Analytics schema
CREATE SCHEMA IF NOT EXISTS analytics;

CREATE TABLE IF NOT EXISTS analytics.monthly_sales_by_product (
    month             DATE,
    product_name      VARCHAR(50),
    gross_revenue     NUMERIC(12,2),
    order_count       INTEGER,
    avg_order_value   NUMERIC(10,2),
    etl_loaded_at     TIMESTAMP,
    PRIMARY KEY (month, product_name)
);
