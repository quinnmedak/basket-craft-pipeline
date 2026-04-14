# Basket Craft Pipeline

An ELT pipeline that pulls sales data from the Basket Craft MySQL database, loads it into PostgreSQL, and transforms it into a monthly sales analytics table. Raw data is also mirrored to an AWS RDS PostgreSQL instance for broader analysis.

## What it does

**Local pipeline:** Extracts three tables from MySQL (`orders`, `order_items`, `products`), loads them raw into a local Postgres instance, then runs a SQL aggregation to produce a `monthly_sales_by_product` table with gross revenue, order count, and average order value grouped by product and month.

**RDS loader:** Extracts all 8 tables from MySQL and loads them as-is into the `public` schema of an AWS RDS PostgreSQL database — no transformations, full reload on each run.

## How it works

```
MySQL (basket_craft)
  └── orders, order_items, products
          │  extract.py
          ▼
Local Postgres — raw schema
  └── raw.orders, raw.order_items, raw.products
          │  monthly_summary.sql
          ▼
Local Postgres — analytics schema
  └── analytics.monthly_sales_by_product


MySQL (basket_craft)
  └── all 8 tables
          │  load_raw_to_rds.py
          ▼
AWS RDS Postgres — public schema
  └── employees, order_item_refunds, order_items,
      orders, products, users,
      website_pageviews, website_sessions
```

Each run does a full reload, so it's safe to re-run.

## Setup

**Prerequisites:** Python 3, Docker

```bash
# 1. Clone and enter the repo
git clone https://github.com/quinnmedak/basket-craft-pipeline.git
cd basket-craft-pipeline

# 2. Create virtual environment and install dependencies
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt

# 3. Configure credentials
cp .env.example .env
# Edit .env and fill in your MySQL credentials
# Postgres values can stay as-is (they match the Docker container)

# 4. Start Postgres
docker compose up -d

# 5. Initialize database schemas
docker exec -i basket-craft-pipeline-postgres-1 psql -U pipeline -d basket_craft \
  < pipeline/sql/create_tables.sql
```

## Running the pipeline

```bash
# Local pipeline (MySQL → local Postgres → analytics)
.venv/bin/python run_pipeline.py

# RDS loader (MySQL → AWS RDS, all tables, public schema)
PYTHONUNBUFFERED=1 .venv/bin/python load_raw_to_rds.py
```

Example output (`run_pipeline.py`):
```
=== Basket Craft ELT Pipeline ===

[1/2] Extracting from MySQL → Postgres raw schema...
  Loaded 32313 rows into raw.orders
  Loaded 40025 rows into raw.order_items
  Loaded 4 rows into raw.products

[2/2] Transforming raw → analytics schema...

Done. 94 rows in analytics.monthly_sales_by_product.
```

Example output (`load_raw_to_rds.py`):
```
Found 8 table(s): employees, order_item_refunds, order_items, orders, products, users, website_pageviews, website_sessions
  employees: 20 rows loaded into RDS public.employees
  ...
  website_sessions: 472871 rows loaded into RDS public.website_sessions
Done.
```

## Running tests

```bash
# Unit and integration tests
.venv/bin/pytest tests/ -v -k "not smoke"

# Full end-to-end smoke test (requires MySQL access, ~20s)
.venv/bin/pytest tests/test_pipeline.py::test_smoke_full_pipeline -v
```

## Environment variables

| Variable | Description |
|---|---|
| `MYSQL_HOST` | MySQL host |
| `MYSQL_PORT` | MySQL port (default 3306) |
| `MYSQL_USER` | MySQL username |
| `MYSQL_PASSWORD` | MySQL password |
| `MYSQL_DATABASE` | MySQL database name |
| `PG_HOST` | Local Postgres host (default `localhost`) |
| `PG_PORT` | Local Postgres port (default `5432`) |
| `PG_USER` | Local Postgres user (default `pipeline`) |
| `PG_PASSWORD` | Local Postgres password (default `pipeline`) |
| `PG_DATABASE` | Local Postgres database (default `basket_craft`) |
| `RDS_HOST` | AWS RDS hostname |
| `RDS_PORT` | RDS port (default 5432) |
| `RDS_USER` | RDS username |
| `RDS_PASSWORD` | RDS password |
| `RDS_DATABASE` | RDS database name |
