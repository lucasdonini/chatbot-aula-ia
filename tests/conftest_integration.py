from collections.abc import Generator
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Callable, ContextManager
from unittest.mock import patch

import pytest
from alembic.command import downgrade, upgrade
from alembic.config import Config as AlembicConfig
from pydantic import SecretStr
from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from testcontainers.postgres import PostgresContainer

from app.domain.model.transaction import Category, TransactionType
from app.infrastructure.postgres.entities.transaction import TransactionORM
from app.infrastructure.postgres.repositories.transaction_repository import (
    SQLAlchemyTransactionRepository,
)
from app.services.transaction_service import TransactionService

ALEMBIC_CFG = AlembicConfig(str(Path(__file__).resolve().parent.parent / "alembic.ini"))


@pytest.fixture(scope="session")
def postgres_container() -> Generator[PostgresContainer, None, None]:
    with PostgresContainer("postgres:16-alpine") as container:
        yield container


@pytest.fixture(scope="session")
def db_url(postgres_container: PostgresContainer) -> str:
    return postgres_container.get_connection_url()


@pytest.fixture(scope="session")
def apply_migrations(db_url: str) -> Generator[None, None, None]:
    with patch("app.infrastructure.settings.settings.postgres_url", SecretStr(db_url)):
        upgrade(ALEMBIC_CFG, "head")
        yield
        downgrade(ALEMBIC_CFG, "base")


@pytest.fixture
def raw_engine(db_url: str) -> Generator:
    engine = create_engine(db_url, pool_pre_ping=True)
    yield engine
    engine.dispose()


@pytest.fixture
def db_session(raw_engine) -> Generator[Session, None, None]:
    connection = raw_engine.connect()
    transaction = connection.begin()
    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    yield session

    session.close()
    transaction.rollback()
    connection.close()


@pytest.fixture
def session_factory(
    db_session: Session,
) -> Callable[[], ContextManager[Session]]:
    @contextmanager
    def factory() -> Generator[Session, None, None]:
        yield db_session

    return factory


@pytest.fixture
def transaction_repository(session_factory) -> SQLAlchemyTransactionRepository:
    return SQLAlchemyTransactionRepository(session_factory=session_factory)


@pytest.fixture
def transaction_service(transaction_repository) -> TransactionService:
    return TransactionService(repository=transaction_repository)


def _insert_seed_transactions(session: Session) -> list[TransactionORM]:
    seeds = [
        TransactionORM(
            amount=5000.00,
            category=Category.OTHER,
            transaction_type=TransactionType.INCOME,
            description="Salário",
            occurred_at=datetime(2026, 6, 1, 8, 0, 0, tzinfo=timezone.utc),
            source_text="Recebi salário de 5000 reais",
        ),
        TransactionORM(
            amount=150.00,
            category=Category.FOOD,
            transaction_type=TransactionType.EXPENSE,
            description="Almoço",
            occurred_at=datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
            source_text="Gastei 150 reais com almoço",
        ),
        TransactionORM(
            amount=3000.00,
            category=Category.OTHER,
            transaction_type=TransactionType.INCOME,
            description="Freela",
            occurred_at=datetime(2026, 6, 2, 14, 0, 0, tzinfo=timezone.utc),
            source_text="Recebi 3000 de freela",
        ),
        TransactionORM(
            amount=50.00,
            category=Category.TRANSPORTATION,
            transaction_type=TransactionType.EXPENSE,
            description="Uber",
            occurred_at=datetime(2026, 6, 2, 18, 0, 0, tzinfo=timezone.utc),
            source_text="Gastei 50 de uber",
        ),
        TransactionORM(
            amount=200.00,
            category=Category.HEALTH,
            transaction_type=TransactionType.EXPENSE,
            description="Farmácia",
            occurred_at=datetime(2026, 6, 3, 10, 0, 0, tzinfo=timezone.utc),
            source_text="Comprei remedio",
        ),
        TransactionORM(
            amount=1000.00,
            category=Category.INVESTMENT,
            transaction_type=TransactionType.TRANSFER,
            description="Investimento",
            occurred_at=datetime(2026, 6, 3, 16, 0, 0, tzinfo=timezone.utc),
            source_text="Transferi 1000 para investimentos",
        ),
    ]
    for orm in seeds:
        session.add(orm)
    session.commit()
    for orm in seeds:
        session.refresh(orm)
    return seeds


@pytest.fixture
def seed_transactions(db_session: Session) -> list[TransactionORM]:
    return _insert_seed_transactions(db_session)
