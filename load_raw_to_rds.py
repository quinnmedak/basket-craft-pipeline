import os
from dotenv import load_dotenv
from psycopg2.extras import execute_values
from pipeline.config import get_mysql_conn, get_rds_conn

load_dotenv()

# Maps MySQL base type names to PostgreSQL types.
MYSQL_TO_PG = {
    "tinyint":    "SMALLINT",
    "smallint":   "SMALLINT",
    "mediumint":  "INTEGER",
    "int":        "INTEGER",
    "bigint":     "BIGINT",
    "float":      "REAL",
    "double":     "DOUBLE PRECISION",
    "decimal":    "NUMERIC",
    "numeric":    "NUMERIC",
    "char":       "TEXT",
    "varchar":    "TEXT",
    "tinytext":   "TEXT",
    "text":       "TEXT",
    "mediumtext": "TEXT",
    "longtext":   "TEXT",
    "date":       "DATE",
    "datetime":   "TIMESTAMP",
    "timestamp":  "TIMESTAMP",
    "time":       "TIME",
    "year":       "SMALLINT",
    "boolean":    "BOOLEAN",
    "bool":       "BOOLEAN",
    "bit":        "BOOLEAN",
    "json":       "JSONB",
    "blob":       "BYTEA",
    "mediumblob": "BYTEA",
    "longblob":   "BYTEA",
    "tinyblob":   "BYTEA",
    "binary":     "BYTEA",
    "varbinary":  "BYTEA",
    "enum":       "TEXT",
    "set":        "TEXT",
}


def pg_type(mysql_col_type):
    """Convert a MySQL column type string to a Postgres type."""
    lower = mysql_col_type.lower()
    # tinyint(1) is MySQL's boolean convention
    if lower.startswith("tinyint(1)"):
        return "BOOLEAN"
    base = lower.split("(")[0].strip()
    return MYSQL_TO_PG.get(base, "TEXT")


def list_tables(mysql_cur):
    mysql_cur.execute("SHOW TABLES;")
    return [list(row.values())[0] for row in mysql_cur.fetchall()]


def get_columns(mysql_cur, table, db_name):
    """Return list of (column_name, mysql_type) ordered by position."""
    mysql_cur.execute(
        "SELECT COLUMN_NAME, COLUMN_TYPE "
        "FROM INFORMATION_SCHEMA.COLUMNS "
        "WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s "
        "ORDER BY ORDINAL_POSITION;",
        (db_name, table),
    )
    return [(row["COLUMN_NAME"], row["COLUMN_TYPE"]) for row in mysql_cur.fetchall()]


def create_table(rds_conn, table, columns):
    """Drop and recreate raw.<table> on RDS with the given columns."""
    col_defs = ", ".join(
        f'"{name}" {pg_type(dtype)}' for name, dtype in columns
    )
    cur = rds_conn.cursor()
    try:
        cur.execute(f"DROP TABLE IF EXISTS public.{table};")
        cur.execute(f"CREATE TABLE public.{table} ({col_defs});")
        rds_conn.commit()
    except Exception:
        rds_conn.rollback()
        raise
    finally:
        cur.close()


def load_rows(mysql_cur, rds_conn, table, columns):
    """SELECT all rows from MySQL and INSERT into RDS raw.<table>."""
    col_names = [col[0] for col in columns]
    col_list = ", ".join(f"`{c}`" for c in col_names)
    pg_col_list = ", ".join(f'"{c}"' for c in col_names)
    placeholders = ", ".join(["%s"] * len(col_names))

    mysql_cur.execute(f"SELECT {col_list} FROM `{table}`;")
    rows = mysql_cur.fetchall()

    cur = rds_conn.cursor()
    try:
        if rows:
            values = [tuple(row[c] for c in col_names) for row in rows]
            execute_values(
                cur,
                f"INSERT INTO public.{table} ({pg_col_list}) VALUES %s",
                values,
                page_size=1000,
            )
        rds_conn.commit()
    except Exception:
        rds_conn.rollback()
        raise
    finally:
        cur.close()

    return len(rows)


def run():
    db_name = os.getenv("MYSQL_DATABASE")
    mysql_conn = get_mysql_conn()
    rds_conn = get_rds_conn()
    try:
        with mysql_conn.cursor() as cur:
            tables = list_tables(cur)
            print(f"Found {len(tables)} table(s): {', '.join(tables)}")
            for table in tables:
                columns = get_columns(cur, table, db_name)
                create_table(rds_conn, table, columns)
                count = load_rows(cur, rds_conn, table, columns)
                print(f"  {table}: {count} rows loaded into RDS public.{table}")
    finally:
        mysql_conn.close()
        rds_conn.close()
    print("Done.")


if __name__ == "__main__":
    run()
