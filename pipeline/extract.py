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
    try:
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
    except Exception:
        pg_conn.rollback()
        raise
    finally:
        cur.close()

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
