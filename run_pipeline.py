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
    try:
        cur.execute("SELECT COUNT(*) FROM analytics.monthly_sales_by_product;")
        row_count = cur.fetchone()[0]
    finally:
        cur.close()
        pg_conn.close()

    print(f"\nDone. {row_count} rows in analytics.monthly_sales_by_product.")

if __name__ == "__main__":
    main()
