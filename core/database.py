# core/database.py
"""
Thin PostgreSQL helper for agents.
This module initializes connection pooling via PostgresPool and provides
a few convenience helpers for queries.

It assumes:
- /database/db_pool.py provides PostgresPool with init_pool/get_conn/return_conn/close_all
- /database/db_config.py contains DB config/environment
"""

from typing import Any, List, Optional
from psycopg2.extras import RealDictCursor
from database.db_pool import PostgresPool
from database.db_config import DBConfig


def init_db_pool(minconn: int = 1, maxconn: int = 10) -> None:
    """Initialize the global Postgres connection pool."""
    PostgresPool.init_pool(minconn=minconn, maxconn=maxconn)
    print("[core.database] Postgres pool initialized.")


def fetch_one(query: str, params: Optional[List[Any]] = None) -> Optional[dict]:
    """Execute SELECT ... and return one row as dict (or None)."""
    conn = PostgresPool.get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params or [])
            row = cur.fetchone()
            # Note: do NOT commit after SELECT
            return dict(row) if row else None
    finally:
        PostgresPool.return_conn(conn)


def fetch_all(query: str, params: Optional[List[Any]] = None) -> List[dict]:
    """Execute SELECT ... and return all rows as list-of-dicts."""
    conn = PostgresPool.get_conn()
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(query, params or [])
            rows = cur.fetchall()
            return [dict(r) for r in rows]
    finally:
        PostgresPool.return_conn(conn)


def execute(query: str, params: Optional[List[Any]] = None) -> None:
    """Execute INSERT/UPDATE/DELETE queries and commit."""
    conn = PostgresPool.get_conn()
    try:
        with conn.cursor() as cur:
            cur.execute(query, params or [])
        conn.commit()
    finally:
        PostgresPool.return_conn(conn)
