import pandas as pd
from snowflake.connector.pandas_tools import write_pandas
from dotenv import load_dotenv
from pipeline.config import get_rds_conn, get_snowflake_conn

load_dotenv()

TABLES = [
    "orders",
    "order_items",
    "products",
    "order_item_refunds",
    "users",
    "employees",
    "website_pageviews",
    "website_sessions",
]


def load_table(rds_conn, sf_conn, table):
    df = pd.read_sql(f"select * from public.{table}", rds_conn)
    success, nchunks, nrows, _ = write_pandas(
        sf_conn,
        df,
        table_name=table,
        overwrite=True,
        quote_identifiers=False,
    )
    return nrows


def run():
    rds_conn = get_rds_conn()
    sf_conn = get_snowflake_conn()
    try:
        for table in TABLES:
            print(f"Loading {table}...", flush=True)
            nrows = load_table(rds_conn, sf_conn, table)
            print(f"  {table}: {nrows} rows loaded into Snowflake raw.{table}")
    finally:
        rds_conn.close()
        sf_conn.close()
    print("Done.")


if __name__ == "__main__":
    run()
