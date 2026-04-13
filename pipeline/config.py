import os
import pymysql
import psycopg2
from dotenv import load_dotenv

load_dotenv()

def get_mysql_conn():
    return pymysql.connect(
        host=os.getenv("MYSQL_HOST"),
        port=int(os.getenv("MYSQL_PORT") or 3306),
        user=os.getenv("MYSQL_USER"),
        password=os.getenv("MYSQL_PASSWORD"),
        database=os.getenv("MYSQL_DATABASE"),
        cursorclass=pymysql.cursors.DictCursor,
    )

def get_pg_conn():
    return psycopg2.connect(
        host=os.getenv("PG_HOST", "localhost"),
        port=int(os.getenv("PG_PORT") or 5432),
        user=os.getenv("PG_USER", "pipeline"),
        password=os.getenv("PG_PASSWORD", "pipeline"),
        dbname=os.getenv("PG_DATABASE", "basket_craft"),
    )

def get_rds_conn():
    return psycopg2.connect(
        host=os.getenv("RDS_HOST"),
        port=int(os.getenv("RDS_PORT") or 5432),
        user=os.getenv("RDS_USER"),
        password=os.getenv("RDS_PASSWORD"),
        dbname=os.getenv("RDS_DATABASE"),
    )
