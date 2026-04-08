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
