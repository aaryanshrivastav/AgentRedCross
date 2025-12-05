# db_pool.py
import psycopg2
from psycopg2.pool import SimpleConnectionPool
from database.db_config import DBConfig


class PostgresPool:
    """Maintains a global connection pool for all agents."""

    pool: SimpleConnectionPool = None

    @classmethod
    def init_pool(cls, minconn=1, maxconn=10):
        """Initialize a PostgreSQL connection pool."""
        if cls.pool is None:
            cls.pool = SimpleConnectionPool(
                minconn=minconn,
                maxconn=maxconn,
                user=DBConfig.USER,
                password=DBConfig.PASSWORD,
                host=DBConfig.HOST,
                port=DBConfig.PORT,
                database=DBConfig.NAME
            )
            print("[DB] Connection pool initialized.")

    @classmethod
    def get_conn(cls):
        if cls.pool is None:
            raise Exception("Database pool not initialized.")
        return cls.pool.getconn()

    @classmethod
    def return_conn(cls, conn):
        """Return a connection to the pool."""
        cls.pool.putconn(conn)

    @classmethod
    def close_all(cls):
        """Close all connections gracefully."""
        if cls.pool:
            cls.pool.closeall()
            print("[DB] Connection pool closed.")
