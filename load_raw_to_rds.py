from pipeline.config import get_mysql_conn, get_rds_conn
from pipeline.extract import extract_table, load_table, EXPECTED_COLUMNS

def run():
    mysql_conn = get_mysql_conn()
    rds_conn = get_rds_conn()
    try:
        with mysql_conn.cursor() as cur:
            for table in ["orders", "order_items", "products"]:
                print(f"Extracting {table}...")
                rows = extract_table(cur, table)
                load_table(rds_conn, table, rows, EXPECTED_COLUMNS[table])
                print(f"  Loaded {len(rows)} rows into RDS raw.{table}")
    finally:
        mysql_conn.close()
        rds_conn.close()

if __name__ == "__main__":
    run()
