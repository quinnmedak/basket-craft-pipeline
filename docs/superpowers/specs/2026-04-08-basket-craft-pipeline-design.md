# Basket Craft ELT Pipeline — Design Spec

**Date:** 2026-04-08

## Overview

An ELT pipeline that extracts sales data from the Basket Craft MySQL database, loads raw tables into a local PostgreSQL instance (Docker), and transforms them into a monthly sales analytics table for a dashboard showing gross revenue, order count, and average order value by product and month.

---

## Architecture

```
MySQL (basket_craft @ db.isba.co)
  └── orders, order_items, products
          │
          ▼
    extract.py (Python)
      Pull raw rows, load into Postgres raw schema
          │
          ▼
PostgreSQL (Docker) — raw schema
  └── raw.orders
  └── raw.order_items
  └── raw.products
          │
          ▼
    transform.py (Python — executes SQL against Postgres)
      Aggregation: group by product × month
          │
          ▼
PostgreSQL (Docker) — analytics schema
  └── analytics.monthly_sales_by_product
```

---

## File Structure

```
basket-craft-pipeline/
├── docker-compose.yml           # Postgres container
├── requirements.txt             # Python deps: pymysql, psycopg2, python-dotenv
├── .env                         # DB credentials (gitignored)
├── run_pipeline.py              # Entry point: calls extract then transform, prints row count
└── pipeline/
    ├── config.py                # MySQL + Postgres connection factories
    ├── extract.py               # Pull from MySQL → load raw.* tables (TRUNCATE + INSERT)
    ├── transform.py             # Execute transform SQL against Postgres
    └── sql/
        ├── create_tables.sql    # CREATE SCHEMA + raw & analytics table definitions
        └── monthly_summary.sql  # Aggregation query → analytics.monthly_sales_by_product
```

---

## Source Schema (MySQL — basket_craft)

Relevant tables:
- **`orders`** — `order_id`, `created_at`, `user_id`, `primary_product_id`, `items_purchased`, `price_usd`, `cogs_usd`
- **`order_items`** — `order_item_id`, `created_at`, `order_id`, `product_id`, `is_primary_item`, `price_usd`, `cogs_usd`
- **`products`** — `product_id`, `created_at`, `product_name`, `description`

4 products: The Original, Valentine's, Birthday, and Holiday Gift Basket. No category taxonomy — product = category.

---

## Destination Schema (PostgreSQL)

### Raw schema (mirrors source)

**`raw.orders`** — `order_id`, `created_at`, `user_id`, `primary_product_id`, `items_purchased`, `price_usd`, `cogs_usd`

**`raw.order_items`** — `order_item_id`, `created_at`, `order_id`, `product_id`, `is_primary_item`, `price_usd`, `cogs_usd`

**`raw.products`** — `product_id`, `created_at`, `product_name`, `description`

### Analytics schema

**`analytics.monthly_sales_by_product`** — built by joining `raw.order_items` + `raw.products` (`raw.orders` is loaded for completeness but not used in this transform)

| column | type | description |
|---|---|---|
| `month` | DATE | First day of month (e.g. 2024-01-01) |
| `product_name` | VARCHAR(50) | e.g. "The Original Gift Basket" |
| `gross_revenue` | NUMERIC(12,2) | SUM of `order_items.price_usd` |
| `order_count` | INT | COUNT DISTINCT `order_id` |
| `avg_order_value` | NUMERIC(10,2) | `gross_revenue / order_count` |
| `etl_loaded_at` | TIMESTAMP | When the pipeline last ran |

Primary key: `(month, product_name)`

---

## Load Strategy

**Idempotent full reload:** every run `TRUNCATE`s the raw tables and the analytics table before inserting. Running the pipeline twice produces identical results — no duplicates, no partial data.

---

## Error Handling

- `try/except` around MySQL and Postgres connections — print clear message and exit on failure
- `try/except` around extract and transform steps — stop on error, do not load partial data
- Column check at start of `extract.py` — compare expected columns against MySQL's actual columns; exit with error on mismatch (guards against schema drift)
- No retries — fix and re-run manually

---

## Validation

`run_pipeline.py` prints the final row count from `analytics.monthly_sales_by_product` after each run as a sanity check. No automated test suite.

---

## Schedule

Daily, via cron. Full reload each run (~32K order_items rows — negligible runtime).
