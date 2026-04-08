# Basket Craft Pipeline

An ELT pipeline that pulls sales data from the Basket Craft MySQL database, loads it into a local PostgreSQL instance, and transforms it into a monthly sales analytics table.

## What it does

Extracts three tables from MySQL (`orders`, `order_items`, `products`), loads them raw into Postgres, then runs a SQL aggregation to produce a `monthly_sales_by_product` table with:

- Gross revenue
- Order count
- Average order value

...grouped by product and month.

## How it works

```
MySQL (basket_craft)
  └── orders, order_items, products
          │  extract.py
          ▼
Postgres — raw schema
  └── raw.orders, raw.order_items, raw.products
          │  monthly_summary.sql
          ▼
Postgres — analytics schema
  └── analytics.monthly_sales_by_product
```

Each run does a full reload (TRUNCATE + INSERT), so it's safe to re-run.

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
.venv/bin/python run_pipeline.py
```

Example output:
```
=== Basket Craft ELT Pipeline ===

[1/2] Extracting from MySQL → Postgres raw schema...
  Loaded 32313 rows into raw.orders
  Loaded 40025 rows into raw.order_items
  Loaded 4 rows into raw.products

[2/2] Transforming raw → analytics schema...

Done. 94 rows in analytics.monthly_sales_by_product.
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
| `PG_HOST` | Postgres host (default `localhost`) |
| `PG_PORT` | Postgres port (default `5432`) |
| `PG_USER` | Postgres user (default `pipeline`) |
| `PG_PASSWORD` | Postgres password (default `pipeline`) |
| `PG_DATABASE` | Postgres database (default `basket_craft`) |
