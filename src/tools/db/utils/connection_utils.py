from psycopg2.extensions import connection, cursor
from src.model.EnvSettings import env
from typing import Generator
from contextlib import contextmanager
import psycopg2


@contextmanager
def get_connection() -> Generator[connection, None, None]:
    conn: connection = psycopg2.connect(env.database_url)
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


@contextmanager
def get_cursor() -> Generator[cursor, None, None]:
    with get_connection() as conn:
        cur: cursor = conn.cursor()
        try:
            yield cur
        finally:
            cur.close()
