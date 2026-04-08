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
