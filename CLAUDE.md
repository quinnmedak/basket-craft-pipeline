# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project

Python ELT pipeline: MySQL (basket_craft) → Postgres raw schema → Postgres analytics schema.
Monthly sales dashboard: gross revenue, order count, avg order value by product and month.

## Source Schema (MySQL — basket_craft)

- `orders` — order_id, created_at, user_id, primary_product_id, items_purchased, price_usd, cogs_usd
- `order_items` — order_item_id, created_at, order_id, product_id, is_primary_item, price_usd, cogs_usd
- `products` — 4 products (Original, Valentine's, Birthday, Holiday Gift Basket); product = category
- `order_item_refunds`, `users`, `employees`, `website_pageviews`, `website_sessions` — additional tables present in MySQL; not used by the core pipeline but loaded to RDS

## Pipeline Architecture

Two separate pipelines share `pipeline/config.py` for connection helpers:

**Local pipeline** (`run_pipeline.py`): MySQL → local Docker Postgres
1. `pipeline/extract.py` — pulls `orders`, `order_items`, `products` from MySQL; validates columns against `EXPECTED_COLUMNS`; TRUNCATEs and INSERTs into `raw.*` in local Postgres
2. `pipeline/sql/monthly_summary.sql` — aggregates `raw.order_items` + `raw.products` into `analytics.monthly_sales_by_product`
3. `pipeline/transform.py` — executes the SQL above against local Postgres

**RDS loader** (`load_raw_to_rds.py`): MySQL → AWS RDS Postgres (`public` schema)
- Discovers all MySQL tables dynamically via `SHOW TABLES` + `INFORMATION_SCHEMA`
- Auto-maps MySQL column types to Postgres types
- Drops and recreates each table in `public.*` on RDS, then loads all rows
- Uses `psycopg2.extras.execute_values` with `page_size=1000` for efficient bulk inserts

Full reload every run. Idempotent: TRUNCATE/DROP+CREATE + INSERT on each run.

## Setup (first time)

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env          # fill in MySQL credentials; Postgres defaults work as-is
docker compose up -d

# Initialize DB schemas before first pipeline run
docker exec -i basket-craft-pipeline-postgres-1 psql -U pipeline -d basket_craft \
  < pipeline/sql/create_tables.sql
```

## Common Commands

```bash
# Start Postgres
docker compose up -d

# Run local pipeline (MySQL → local Docker Postgres)
.venv/bin/python run_pipeline.py

# Load all MySQL tables to AWS RDS (public schema)
PYTHONUNBUFFERED=1 .venv/bin/python load_raw_to_rds.py

# Run all tests (excludes smoke)
.venv/bin/pytest tests/ -v -k "not smoke"

# Run a single test
.venv/bin/pytest tests/test_pipeline.py::test_transform_output -v

# Run smoke test (hits real MySQL — slow)
.venv/bin/pytest tests/test_pipeline.py::test_smoke_full_pipeline -v
```

## Environment

Credentials in `.env` (gitignored). Copy `.env.example` to `.env` and fill in values.
- MySQL vars: `MYSQL_HOST`, `MYSQL_PORT`, `MYSQL_USER`, `MYSQL_PASSWORD`, `MYSQL_DATABASE`
- Local Postgres vars: `PG_HOST`, `PG_PORT`, `PG_USER`, `PG_PASSWORD`, `PG_DATABASE` (defaults match docker-compose)
- RDS vars: `RDS_HOST`, `RDS_PORT`, `RDS_USER`, `RDS_PASSWORD`, `RDS_DATABASE`

## Database Connection Details

**Local Docker Postgres**
- Host: `localhost:5432`
- Database: `basket_craft`
- User: `pipeline` / Password: `pipeline`
- Schemas: `raw` (source tables), `analytics` (aggregated output)
- Started with `docker compose up -d`

**AWS RDS PostgreSQL**
- Host: `basket-craft-db.cw5mgk6qsvia.us-east-1.rds.amazonaws.com`
- Port: `5432`
- Database: `basket_craft`
- User: `student` (password in `.env`)
- Schema: `public` — all 8 MySQL tables loaded as-is via `load_raw_to_rds.py`
- Connect via psql: `psql -h basket-craft-db.cw5mgk6qsvia.us-east-1.rds.amazonaws.com -U student -d basket_craft`

## Tests

Tests in `tests/test_pipeline.py` run against local Docker Postgres, not MySQL or RDS. `conftest.py` auto-runs `create_tables.sql` via the `create_tables` session fixture before any test. The `seeded_raw` fixture inserts minimal fixture rows and cleans up after the session. Always use `PYTHONUNBUFFERED=1` when running scripts that connect to RDS to avoid silent hangs from stdout buffering.
