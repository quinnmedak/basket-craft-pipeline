import pytest
from pipeline.extract import check_columns
from pipeline.transform import run_transform

def test_column_check_passes_with_correct_columns():
    actual = ["order_id", "created_at", "user_id", "primary_product_id", "items_purchased", "price_usd", "cogs_usd"]
    expected = ["order_id", "created_at", "user_id", "primary_product_id", "items_purchased", "price_usd", "cogs_usd"]
    check_columns("orders", actual, expected)  # should not raise

def test_column_check_fails_with_missing_column():
    actual = ["order_id", "created_at"]
    expected = ["order_id", "created_at", "user_id"]
    with pytest.raises(ValueError, match="Schema drift"):
        check_columns("orders", actual, expected)

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

def test_transform_output(pg_conn, seeded_raw):
    run_transform(pg_conn)

    cur = pg_conn.cursor()
    try:
        cur.execute("""
            SELECT month, product_name, gross_revenue, order_count, avg_order_value, etl_loaded_at
            FROM analytics.monthly_sales_by_product
            ORDER BY month, product_name;
        """)
        rows = cur.fetchall()
    finally:
        cur.close()

    assert len(rows) == 2

    jan = rows[0]
    assert str(jan[0]) == "2024-01-01"
    assert jan[1] == "The Original Gift Basket"
    assert float(jan[2]) == pytest.approx(100.00)
    assert jan[3] == 2
    assert float(jan[4]) == pytest.approx(50.00)
    assert jan[5] is not None

    feb = rows[1]
    assert str(feb[0]) == "2024-02-01"
    assert feb[1] == "The Birthday Gift Basket"
    assert float(feb[2]) == pytest.approx(40.00)
    assert feb[3] == 1
    assert float(feb[4]) == pytest.approx(40.00)
    assert feb[5] is not None

def test_smoke_full_pipeline(pg_conn):
    """Runs full pipeline against real MySQL and Postgres. Slow — run manually."""
    from pipeline.extract import run_extract
    from pipeline.transform import run_transform

    run_extract()
    run_transform(pg_conn)

    cur = pg_conn.cursor()
    try:
        cur.execute("""
            SELECT month, product_name, gross_revenue, order_count, avg_order_value
            FROM analytics.monthly_sales_by_product;
        """)
        rows = cur.fetchall()
    finally:
        cur.close()

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
