import os
import pytest
from pipeline.config import get_pg_conn


@pytest.fixture(scope="session")
def pg_conn():
    conn = get_pg_conn()
    yield conn
    conn.close()

@pytest.fixture(scope="session", autouse=True)
def create_tables(pg_conn):
    sql_path = os.path.join(os.path.dirname(__file__), "..", "pipeline", "sql", "create_tables.sql")
    with open(sql_path) as f:
        sql = f.read()
    cur = pg_conn.cursor()
    try:
        cur.execute(sql)
        pg_conn.commit()
    except Exception as e:
        pg_conn.rollback()
        pytest.fail(f"Failed to create tables: {e}")
    finally:
        cur.close()
    yield

@pytest.fixture(scope="session")
def seeded_raw(pg_conn):
    cur = pg_conn.cursor()
    try:
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
    except Exception:
        pg_conn.rollback()
        raise
    finally:
        cur.close()
    yield
    cur = pg_conn.cursor()
    try:
        cur.execute("TRUNCATE raw.products, raw.order_items, raw.orders CASCADE;")
        pg_conn.commit()
    finally:
        cur.close()
