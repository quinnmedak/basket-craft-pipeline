# Basket Craft ELT Pipeline Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build an ELT pipeline that extracts sales data from MySQL, loads raw tables into local PostgreSQL (Docker), and transforms them into a monthly sales analytics table.

**Architecture:** Python extracts raw `orders`, `order_items`, and `products` from MySQL and loads them into a `raw` schema in Postgres. A SQL transform then aggregates those raw tables into `analytics.monthly_sales_by_product`. Full reload on every run — TRUNCATE then INSERT.

**Tech Stack:** Python 3, pymysql, psycopg2-binary, python-dotenv, PostgreSQL 15 (Docker), pytest

---

### Task 1: Project scaffold and Docker Postgres

**Files:**
- Create: `docker-compose.yml`
- Create: `requirements.txt`
- Create: `pipeline/__init__.py`

- [ ] **Step 1: Create `docker-compose.yml`**

```yaml
services:
  postgres:
    image: postgres:15
    environment:
      POSTGRES_USER: pipeline
      POSTGRES_PASSWORD: pipeline
      POSTGRES_DB: basket_craft
    ports:
      - "5432:5432"
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

- [ ] **Step 2: Create `requirements.txt`**

```
pymysql==1.1.1
psycopg2-binary==2.9.9
python-dotenv==1.0.1
pytest==8.2.0
```

- [ ] **Step 3: Create `pipeline/__init__.py`** (empty file)

```python
```

- [ ] **Step 4: Start Postgres and verify**

```bash
docker compose up -d
docker compose ps
```

Expected: `basket-craft-pipeline-postgres-1` with status `running`.

- [ ] **Step 5: Install Python deps**

```bash
pip install -r requirements.txt
```

Expected: all packages install without error.

- [ ] **Step 6: Commit**

```bash
git add docker-compose.yml requirements.txt pipeline/__init__.py
git commit -m "feat: project scaffold, Docker Postgres, Python deps"
```

---

### Task 2: Database connection config

**Files:**
- Create: `pipeline/config.py`
- Create: `tests/__init__.py`
- Create: `tests/conftest.py`

- [ ] **Step 1: Write the failing test**

Create `tests/__init__.py` (empty), then create `tests/conftest.py`:

```python
import os
import pytest
import psycopg2
from dotenv import load_dotenv

load_dotenv()

@pytest.fixture(scope="session")
def pg_conn():
    conn = psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", 5432)),
        user=os.getenv("PG_USER", "pipeline"),
        password=os.getenv("PG_PASSWORD", "pipeline"),
        dbname=os.getenv("PG_DATABASE", "basket_craft"),
    )
    yield conn
    conn.close()
```

Then write `tests/test_pipeline.py` with the first test:

```python
def test_postgres_connection(pg_conn):
    cur = pg_conn.cursor()
    cur.execute("SELECT 1;")
    assert cur.fetchone()[0] == 1
```

- [ ] **Step 2: Run test to verify it fails**

```bash
pytest tests/test_pipeline.py::test_postgres_connection -v
```

Expected: FAIL — `pipeline.config` not importable or connection refused.

- [ ] **Step 3: Create `pipeline/config.py`**

```python
import os
import pymysql
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_mysql_conn():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT", 3306)),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        cursorclass=pymysql.cursors.DictCursor,
    )

def get_pg_conn():
    return psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT", 5432)),
        user=os.getenv("PG_USER", "pipeline"),
        password=os.getenv("PG_PASSWORD", "pipeline"),
        dbname=os.getenv("PG_DATABASE", "basket_craft"),
    )
```

- [ ] **Step 4: Add Postgres vars to `.env`**

Append to your existing `.env`:

```
PG_HOST=localhost
PG_PORT=5432
PG_USER=pipeline
PG_PASSWORD=pipeline
PG_DATABASE=basket_craft
```

- [ ] **Step 5: Run test to verify it passes**

```bash
pytest tests/test_pipeline.py::test_postgres_connection -v
```

Expected: PASS.

- [ ] **Step 6: Commit**

```bash
git add pipeline/config.py pipeline/__init__.py tests/__init__.py tests/conftest.py tests/test_pipeline.py
git commit -m "feat: DB connection config and Postgres connection test"
```

---

### Task 3: SQL — create schemas and raw tables

**Files:**
- Create: `pipeline/sql/create_tables.sql`

- [ ] **Step 1: Create `pipeline/sql/create_tables.sql`**

```sql
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
```

- [ ] **Step 2: Write a test that runs the SQL**

Add to `tests/conftest.py`:

```python
@pytest.fixture(scope="session", autouse=True)
def create_tables(pg_conn):
    sql_path = os.path.join(os.path.dirname(__file__), "..", "pipeline", "sql", "create_tables.sql")
    with open(sql_path) as f:
        sql = f.read()
    cur = pg_conn.cursor()
    cur.execute(sql)
    pg_conn.commit()
```

Add to `tests/test_pipeline.py`:

```python
def test_raw_tables_exist(pg_conn):
    cur = pg_conn.cursor()
    for table in ["raw.orders", "raw.order_items", "raw.products", "analytics.monthly_sales_by_product"]:
        schema, tbl = table.split(".")
        cur.execute(
            "SELECT 1 FROM information_schema.tables WHERE table_schema=%s AND table_name=%s",
            (schema, tbl),
        )
        assert cur.fetchone() is not None, f"{table} not found"
```

- [ ] **Step 3: Run test to verify it passes**

```bash
pytest tests/test_pipeline.py::test_raw_tables_exist -v
```

Expected: PASS — all four tables exist.

- [ ] **Step 4: Commit**

```bash
git add pipeline/sql/create_tables.sql tests/conftest.py tests/test_pipeline.py
git commit -m "feat: SQL to create raw and analytics schemas/tables"
```

---

### Task 4: Extract — MySQL to Postgres raw schema

**Files:**
- Create: `pipeline/extract.py`

- [ ] **Step 1: Write the failing test for the column check**

Add to `tests/test_pipeline.py`:

```python
from pipeline.extract import check_columns

def test_column_check_passes_with_correct_columns():
    actual = ["order_id", "created_at", "user_id", "primary_product_id", "items_purchased", "price_usd", "cogs_usd"]
    expected = ["order_id", "created_at", "user_id", "primary_product_id", "items_purchased", "price_usd", "cogs_usd"]
    check_columns("orders", actual, expected)  # should not raise

def test_column_check_fails_with_missing_column():
    import pytest
    actual = ["order_id", "created_at"]
    expected = ["order_id", "created_at", "user_id"]
    with pytest.raises(ValueError, match="Schema drift"):
        check_columns("orders", actual, expected)
```

- [ ] **Step 2: Run tests to verify they fail**

```bash
pytest tests/test_pipeline.py::test_column_check_passes_with_correct_columns tests/test_pipeline.py::test_column_check_fails_with_missing_column -v
```

Expected: FAIL — `cannot import name 'check_columns'`.

- [ ] **Step 3: Create `pipeline/extract.py`**

```python
from datetime import datetime
import pymysql.cursors
from pipeline.config import get_mysql_conn, get_pg_conn

EXPECTED_COLUMNS = {
    "orders": ["order_id", "created_at", "user_id", "primary_product_id", "items_purchased", "price_usd", "cogs_usd"],
    "order_items": ["order_item_id", "created_at", "order_id", "product_id", "is_primary_item", "price_usd", "cogs_usd"],
    "products": ["product_id", "created_at", "product_name", "description"],
}

def check_columns(table_name, actual_columns, expected_columns):
    missing = set(expected_columns) - set(actual_columns)
    if missing:
        raise ValueError(f"Schema drift in {table_name}: missing columns {missing}")

def extract_table(mysql_cur, table_name):
    mysql_cur.execute(f"SELECT * FROM {table_name} LIMIT 1;")
    mysql_cur.fetchall()
    actual = [col[0] for col in mysql_cur.description]
    check_columns(table_name, actual, EXPECTED_COLUMNS[table_name])

    mysql_cur.execute(f"SELECT {', '.join(EXPECTED_COLUMNS[table_name])} FROM {table_name};")
    return mysql_cur.fetchall()

def load_table(pg_conn, table_name, rows, columns):
    cur = pg_conn.cursor()
    cur.execute(f"TRUNCATE raw.{table_name};")
    if rows:
        placeholders = ", ".join(["%s"] * len(columns))
        col_list = ", ".join(columns)
        values = [tuple(row[c] for c in columns) for row in rows]
        cur.executemany(
            f"INSERT INTO raw.{table_name} ({col_list}) VALUES ({placeholders});",
            values,
        )
    pg_conn.commit()

def run_extract():
    mysql_conn = get_mysql_conn()
    pg_conn = get_pg_conn()
    try:
        with mysql_conn.cursor() as cur:
            for table in ["orders", "order_items", "products"]:
                print(f"Extracting {table}...")
                rows = extract_table(cur, table)
                load_table(pg_conn, table, rows, EXPECTED_COLUMNS[table])
                print(f"  Loaded {len(rows)} rows into raw.{table}")
    finally:
        mysql_conn.close()
        pg_conn.close()
```

- [ ] **Step 4: Run column check tests to verify they pass**

```bash
pytest tests/test_pipeline.py::test_column_check_passes_with_correct_columns tests/test_pipeline.py::test_column_check_fails_with_missing_column -v
```

Expected: PASS.

- [ ] **Step 5: Write integration test for extract**

Add to `tests/conftest.py`:

```python
import psycopg2.extras

@pytest.fixture(scope="session")
def seeded_raw(pg_conn):
    cur = pg_conn.cursor()
    cur.execute("TRUNCATE raw.products, raw.order_items, raw.orders CASCADE;")
    cur.execute("""
        INSERT INTO raw.products (product_id, created_at, product_name, description)
        VALUES
            (1, '2023-01-01', 'The Original Gift Basket', 'Original'),
            (2, '2023-01-01', 'The Birthday Gift Basket', 'Birthday');
    """)
    cur.execute("""
        INSERT INTO raw.order_items (order_item_id, created_at, order_id, product_id, is_primary_item, price_usd, cogs_usd)
        VALUES
            (1, '2024-01-15', 101, 1, 1, 50.00, 20.00),
            (2, '2024-01-20', 102, 1, 1, 50.00, 20.00),
            (3, '2024-02-10', 103, 2, 1, 40.00, 15.00);
    """)
    pg_conn.commit()
    yield
    cur.execute("TRUNCATE raw.products, raw.order_items, raw.orders CASCADE;")
    pg_conn.commit()
```

- [ ] **Step 6: Commit**

```bash
git add pipeline/extract.py tests/conftest.py tests/test_pipeline.py
git commit -m "feat: extract MySQL tables into Postgres raw schema with column drift check"
```

---

### Task 5: SQL — monthly summary transform

**Files:**
- Create: `pipeline/sql/monthly_summary.sql`

- [ ] **Step 1: Create `pipeline/sql/monthly_summary.sql`**

```sql
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
```

- [ ] **Step 2: Write a failing test for transform correctness**

Add to `tests/test_pipeline.py`:

```python
from pipeline.transform import run_transform

def test_transform_output(pg_conn, seeded_raw):
    run_transform(pg_conn)

    cur = pg_conn.cursor()
    cur.execute("SELECT month, product_name, gross_revenue, order_count, avg_order_value FROM analytics.monthly_sales_by_product ORDER BY month, product_name;")
    rows = cur.fetchall()

    assert len(rows) == 2

    jan = rows[0]
    assert str(jan[0]) == "2024-01-01"
    assert jan[1] == "The Original Gift Basket"
    assert float(jan[2]) == 100.00
    assert jan[3] == 2
    assert float(jan[4]) == 50.00

    feb = rows[1]
    assert str(feb[0]) == "2024-02-01"
    assert feb[1] == "The Birthday Gift Basket"
    assert float(feb[2]) == 40.00
    assert feb[3] == 1
    assert float(feb[4]) == 40.00
```

- [ ] **Step 3: Run test to verify it fails**

```bash
pytest tests/test_pipeline.py::test_transform_output -v
```

Expected: FAIL — `cannot import name 'run_transform'`.

- [ ] **Step 4: Commit SQL**

```bash
git add pipeline/sql/monthly_summary.sql tests/test_pipeline.py
git commit -m "feat: monthly summary transform SQL and failing test"
```

---

### Task 6: Transform — execute SQL against Postgres

**Files:**
- Create: `pipeline/transform.py`

- [ ] **Step 1: Create `pipeline/transform.py`**

```python
import os
from pipeline.config import get_pg_conn

def run_transform(pg_conn=None):
    close_conn = False
    if pg_conn is None:
        pg_conn = get_pg_conn()
        close_conn = True
    try:
        sql_path = os.path.join(os.path.dirname(__file__), "sql", "monthly_summary.sql")
        with open(sql_path) as f:
            sql = f.read()
        cur = pg_conn.cursor()
        cur.execute(sql)
        pg_conn.commit()
    finally:
        if close_conn:
            pg_conn.close()
```

- [ ] **Step 2: Run transform test to verify it passes**

```bash
pytest tests/test_pipeline.py::test_transform_output -v
```

Expected: PASS.

- [ ] **Step 3: Commit**

```bash
git add pipeline/transform.py
git commit -m "feat: transform module executes monthly summary SQL against Postgres"
```

---

### Task 7: Pipeline entry point

**Files:**
- Create: `run_pipeline.py`

- [ ] **Step 1: Create `run_pipeline.py`**

```python
import sys
from pipeline.config import get_pg_conn
from pipeline.extract import run_extract
from pipeline.transform import run_transform

def main():
    print("=== Basket Craft ELT Pipeline ===")

    print("\n[1/2] Extracting from MySQL → Postgres raw schema...")
    try:
        run_extract()
    except Exception as e:
        print(f"ERROR during extract: {e}")
        sys.exit(1)

    print("\n[2/2] Transforming raw → analytics schema...")
    try:
        run_transform()
    except Exception as e:
        print(f"ERROR during transform: {e}")
        sys.exit(1)

    pg_conn = get_pg_conn()
    cur = pg_conn.cursor()
    cur.execute("SELECT COUNT(*) FROM analytics.monthly_sales_by_product;")
    row_count = cur.fetchone()[0]
    pg_conn.close()

    print(f"\nDone. {row_count} rows in analytics.monthly_sales_by_product.")

if __name__ == "__main__":
    main()
```

- [ ] **Step 2: Run the full pipeline**

```bash
python run_pipeline.py
```

Expected output:
```
=== Basket Craft ELT Pipeline ===

[1/2] Extracting from MySQL → Postgres raw schema...
  Loaded 32313 rows into raw.orders
  Loaded XXXXX rows into raw.order_items
  Loaded 4 rows into raw.products

[2/2] Transforming raw → analytics schema...

Done. XX rows in analytics.monthly_sales_by_product.
```

- [ ] **Step 3: Commit**

```bash
git add run_pipeline.py
git commit -m "feat: pipeline entry point with extract, transform, and row count validation"
```

---

### Task 8: Smoke test

**Files:**
- Modify: `tests/test_pipeline.py`

- [ ] **Step 1: Add smoke test to `tests/test_pipeline.py`**

```python
def test_smoke_full_pipeline(pg_conn):
    """Runs full pipeline against real MySQL and Postgres. Slow — run manually."""
    from pipeline.extract import run_extract
    from pipeline.transform import run_transform

    run_extract()
    run_transform(pg_conn)

    cur = pg_conn.cursor()
    cur.execute("""
        SELECT month, product_name, gross_revenue, order_count, avg_order_value
        FROM analytics.monthly_sales_by_product;
    """)
    rows = cur.fetchall()

    assert len(rows) > 0, "analytics table is empty"

    for row in rows:
        month, product_name, gross_revenue, order_count, avg_order_value = row
        assert month is not None
        assert product_name is not None
        assert gross_revenue is not None
        assert order_count > 0
        assert avg_order_value is not None
        expected_aov = round(float(gross_revenue) / float(order_count), 2)
        assert abs(float(avg_order_value) - expected_aov) < 0.01, \
            f"AOV mismatch for {product_name} {month}: got {avg_order_value}, expected {expected_aov}"
```

- [ ] **Step 2: Run smoke test**

```bash
pytest tests/test_pipeline.py::test_smoke_full_pipeline -v
```

Expected: PASS — rows present, no NULLs, AOV matches revenue / order_count.

- [ ] **Step 3: Run full test suite**

```bash
pytest tests/ -v
```

Expected: all tests PASS.

- [ ] **Step 4: Commit**

```bash
git add tests/test_pipeline.py
git commit -m "test: smoke test for full pipeline run"
```

---

### Task 9: CLAUDE.md

**Files:**
- Create: `CLAUDE.md`

- [ ] **Step 1: Create `CLAUDE.md`**

```markdown
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
python run_pipeline.py

# Run tests (unit + integration, excludes smoke)
pytest tests/ -v -k "not smoke"

# Run smoke test (hits real MySQL — slow)
pytest tests/test_pipeline.py::test_smoke_full_pipeline -v
```

## Environment

Credentials in `.env` (gitignored). MySQL vars: MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE. Postgres vars: PG_HOST, PG_PORT, PG_USER, PG_PASSWORD, PG_DATABASE.
```

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: add CLAUDE.md"
```
