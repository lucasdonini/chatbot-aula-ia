import logging
from contextlib import contextmanager
from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker

from ..settings import settings

logger = logging.getLogger(__name__)

engine = create_engine(settings.postgres_url, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False)


@contextmanager
def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    logger.debug("Postgres session opened")
    try:
        yield db
    except Exception:
        db.rollback()
        logger.exception("Postgres session rolled back due to an error")
        raise
    finally:
        db.close()
        logger.debug("Postgres session closed")
