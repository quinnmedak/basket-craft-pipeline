def test_postgres_connection(pg_conn):
    cur = pg_conn.cursor()
    cur.execute("SELECT 1;")
    assert cur.fetchone()[0] == 1
