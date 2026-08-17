from contextlib import contextmanager
from datetime import date, datetime, timezone
from typing import Callable, ContextManager
from unittest.mock import MagicMock, create_autospec
from uuid import uuid4

import pytest
from sqlalchemy.orm import Session


def _patch_create_agent_model_edge():
    """Fix LangChain + LangGraph 1.1.6 incompatibility in `create_agent`."""
    import langchain.agents.factory as factory

    original = factory._make_model_to_tools_edge

    def _patched_make_edge(
        *, model_destination, structured_output_tools, end_destination
    ):
        edge_fn = original(
            model_destination=model_destination,
            structured_output_tools=structured_output_tools,
            end_destination=end_destination,
        )

        def _safe_edge(state):
            result = edge_fn(state)
            if isinstance(result, str) and result == model_destination:
                return end_destination
            return result

        return _safe_edge

    factory._make_model_to_tools_edge = _patched_make_edge


_patch_create_agent_model_edge()

pytest_plugins = ["tests.conftest_integration"]  # noqa: E402

from app.infrastructure.agents.schema.transaction_query_params import (  # noqa: E402
    TransactionQueryParams,
)
from app.infrastructure.agents.schema.update_transaction_params import (  # noqa: E402
    UpdateTransactionParams,
    UpdateTransactionQuery,
)
from app.infrastructure.repositories.transaction_repository import (  # noqa: E402
    TransactionRepository,
)
from app.model.transaction import Category, Transaction, TransactionType  # noqa: E402
from app.services.transaction_service import TransactionService  # noqa: E402


@pytest.fixture
def sample_transaction() -> Transaction:
    return Transaction(
        amount=150.50,
        category=Category.FOOD,
        transaction_type=TransactionType.EXPENSE,
        description="Almoço no restaurante",
        payment_method="dinheiro",
        occurred_at=datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc),
        source_text="Gastei 150 reais com almoço",
        is_canceled=False,
    )


@pytest.fixture
def sample_transaction_with_id(sample_transaction) -> Transaction:
    t = sample_transaction.model_copy()
    t.occurred_at = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    t.updated_at = datetime(2026, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    return t


@pytest.fixture
def sample_query_params() -> TransactionQueryParams:
    return TransactionQueryParams(
        source_text="almoço",
        occurred_at_start=date(2026, 1, 1),
        occurred_at_end=date(2026, 12, 31),
        category=Category.FOOD,
        transaction_type=TransactionType.EXPENSE,
        limit=10,
    )


@pytest.fixture
def sample_update_params_by_id() -> UpdateTransactionParams:
    return UpdateTransactionParams(
        query=UpdateTransactionQuery(id=uuid4()),
        amount=200.00,
        description="Atualizado",
    )


@pytest.fixture
def sample_update_params_by_match() -> UpdateTransactionParams:
    return UpdateTransactionParams(
        query=UpdateTransactionQuery(
            match_text="almoço",
            date_local=date(2026, 6, 1),
        ),
        amount=200.00,
    )


@pytest.fixture
def sample_update_params_empty() -> UpdateTransactionParams:
    return UpdateTransactionParams(
        query=UpdateTransactionQuery(
            match_text="almoço",
            date_local=date(2026, 6, 1),
        ),
    )


@pytest.fixture
def mock_session() -> MagicMock:
    return create_autospec(Session, instance=True)


@pytest.fixture
def mock_session_factory(mock_session) -> Callable[[], ContextManager[Session]]:
    @contextmanager
    def factory():
        yield mock_session

    return factory


@pytest.fixture
def repository(mock_session_factory) -> TransactionRepository:
    return TransactionRepository(session_factory=mock_session_factory)


@pytest.fixture
def mock_repository() -> MagicMock:
    return create_autospec(TransactionRepository, instance=True)


@pytest.fixture
def service(mock_repository: MagicMock) -> TransactionService:
    return TransactionService(repository=mock_repository)


@pytest.fixture
def sample_transactions_list() -> list[Transaction]:
    return [
        Transaction(
            amount=1000.00,
            category=Category.OTHER,
            transaction_type=TransactionType.INCOME,
            description="Salário",
            occurred_at=datetime(2026, 6, 1, 8, 0, 0, tzinfo=timezone.utc),
            source_text="Recebi salário",
        ),
        Transaction(
            amount=50.00,
            category=Category.FOOD,
            transaction_type=TransactionType.EXPENSE,
            description="Jantar",
            occurred_at=datetime(2026, 6, 2, 20, 0, 0, tzinfo=timezone.utc),
            source_text="Gastei 50 no jantar",
        ),
    ]
