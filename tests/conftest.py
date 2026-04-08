import pytest
from pipeline.config import get_pg_conn

@pytest.fixture(scope="session")
def pg_conn():
    conn = get_pg_conn()
    yield conn
    conn.close()
