import logging

from psycopg2.extensions import connection, cursor
from src.model.env import env
from typing import Generator
from contextlib import contextmanager
import psycopg2

logger = logging.getLogger(__name__)


@contextmanager
def get_connection() -> Generator[connection, None, None]:
    conn: connection = psycopg2.connect(env.database_url)
    try:
        logger.info("Connection opened")
        yield conn

        conn.commit()
        logger.info("Connection commited")

    except Exception:
        conn.rollback()
        logger.exception("Connection rolled-back")
        raise

    finally:
        conn.close()
        logger.info("Connection closed")


@contextmanager
def get_cursor() -> Generator[cursor, None, None]:
    with get_connection() as conn:
        cur: cursor = conn.cursor()
        try:
            logger.info("Cursor created")
            yield cur

        finally:
            cur.close()
            logger.info("Cursor closed")
