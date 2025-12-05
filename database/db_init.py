# db_init.py
import psycopg2
from database.db_config import DBConfig

SCHEMA_PATH = "database/hospital_schema.sql"


def init_database():
    """Reads SQL schema file and executes it in PostgreSQL."""
    try:
        conn = psycopg2.connect(
            user=DBConfig.USER,
            password=DBConfig.PASSWORD,
            host=DBConfig.HOST,
            port=DBConfig.PORT,
            database=DBConfig.NAME,
        )
        cursor = conn.cursor()

        with open(SCHEMA_PATH, "r") as file:
            schema_sql = file.read()

        cursor.execute(schema_sql)
        conn.commit()
        conn.close()

        print("[DB] Schema initialized successfully.")

    except Exception as e:
        print("[DB INIT ERROR]", str(e))
        raise
