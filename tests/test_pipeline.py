def test_postgres_connection(pg_conn):
    cur = pg_conn.cursor()
    try:
        cur.execute("SELECT 1;")
        assert cur.fetchone()[0] == 1
    finally:
        cur.close()

def test_raw_tables_exist(pg_conn):
    cur = pg_conn.cursor()
    try:
        for table in ["raw.orders", "raw.order_items", "raw.products", "analytics.monthly_sales_by_product"]:
            schema, tbl = table.split(".")
            cur.execute(
                "SELECT 1 FROM information_schema.tables WHERE table_schema=%s AND table_name=%s",
                (schema, tbl),
            )
            assert cur.fetchone() is not None, f"{table} not found"
    finally:
        cur.close()
