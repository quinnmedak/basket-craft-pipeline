# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Python ELT pipeline: MySQL (basket_craft) → Postgres raw schema → Postgres analytics schema.
Monthly sales dashboard: gross revenue, order count, avg order value by product and month.

## Source Schema (MySQL — basket_craft)

- `orders` — order_id, created_at, user_id, primary_product_id, items_purchased, price_usd, cogs_usd
- `order_items` — order_item_id, created_at, order_id, product_id, is_primary_item, price_usd, cogs_usd
- `products` — 4 products (Original, Valentine's, Birthday, Holiday Gift Basket); product = category

## Pipeline Architecture

1. `pipeline/extract.py` — pulls raw tables from MySQL, TRUNCATEs and INSERTs into `raw.*` in Postgres
2. `pipeline/sql/monthly_summary.sql` — aggregates `raw.order_items` + `raw.products` into `analytics.monthly_sales_by_product`
3. `pipeline/transform.py` — executes the SQL above
4. `run_pipeline.py` — entry point: extract → transform → print row count

Full reload every run. Idempotent: TRUNCATE + INSERT on each run.

## Common Commands

```bash
# Start Postgres
docker compose up -d

# Run pipeline
.venv/bin/python run_pipeline.py

# Run tests (unit + integration, excludes smoke)
.venv/bin/pytest tests/ -v -k "not smoke"

# Run smoke test (hits real MySQL — slow)
.venv/bin/pytest tests/test_pipeline.py::test_smoke_full_pipeline -v
```

## Environment

Credentials in `.env` (gitignored). Copy `.env.example` to `.env` and fill in values.
MySQL vars: MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE.
Postgres vars: PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DATABASE.
