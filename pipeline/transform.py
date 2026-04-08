import os
from pipeline.config import get_pg_conn

def run_transform(pg_conn=None):
    close_conn = False
    if pg_conn is None:
        pg_conn = get_pg_conn()
        close_conn = True
    try:
        sql_path = os.path.join(os.path.dirname(__file__), "sql", "monthly_summary.sql")
        with open(sql_path) as f:
            sql = f.read()
        cur = pg_conn.cursor()
        try:
            cur.execute(sql)
            pg_conn.commit()
        except Exception:
            pg_conn.rollback()
            raise
        finally:
            cur.close()
    finally:
        if close_conn:
            pg_conn.close()
