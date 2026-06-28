from datetime import date, datetime, timezone
from unittest.mock import MagicMock
from uuid import uuid4

import pytest

from src.model.transaction import Category, Transaction, TransactionType
from src.model.transaction_query_params import TransactionQueryParams
from src.model.update_transaction_params import UpdateTransactionParams


class TestSumAmountsByTransactionType:
    def test_sum_no_filters(self, repository, mock_session):
        mock_session.scalar.return_value = 1500.50

        result = repository.sum_amounts_by_transaction_type(TransactionType.INCOME)

        assert result == 1500.50
        assert mock_session.scalar.called

    def test_sum_with_period(self, repository, mock_session):
        mock_session.scalar.return_value = 500.0
        start = datetime(2026, 1, 1, tzinfo=timezone.utc)
        end = datetime(2026, 6, 1, tzinfo=timezone.utc)

        result = repository.sum_amounts_by_transaction_type(
            TransactionType.EXPENSE, period_start=start, period_end=end
        )

        assert result == 500.0

    def test_sum_returns_zero_for_no_results(self, repository, mock_session):
        mock_session.scalar.return_value = 0

        result = repository.sum_amounts_by_transaction_type(TransactionType.TRANSFER)

        assert result == 0.0

    def test_sum_uses_coalesce(self, repository, mock_session):
        mock_session.scalar.return_value = 0

        repository.sum_amounts_by_transaction_type(TransactionType.INCOME)

        stmt = mock_session.scalar.call_args[0][0]
        compiled = str(stmt.compile(compile_kwargs={"literal_binds": True}))
        assert "coalesce" in compiled.lower()


class TestFind:
    def test_find_with_params(self, repository, mock_session):

        params = TransactionQueryParams(
            source_text="almoço",
            category=Category.FOOD,
            limit=10,
        )
        mock_session.scalars.return_value.all.return_value = []

        result = repository.find(params)

        assert result == []

    def test_find_empty_no_results(self, repository, mock_session):
        params = TransactionQueryParams(source_text="inexistente")
        mock_session.scalars.return_value.all.return_value = []

        result = repository.find(params)

        assert result == []

    def test_find_limit_zero(self, repository, mock_session):
        params = TransactionQueryParams(limit=0)

        result = repository.find(params)

        assert result == []
        mock_session.scalars.assert_not_called()

    def test_find_returns_correct_amount(self, repository, mock_session):
        orm_objects = []
        for i in range(3):
            orm = MagicMock()
            orm.amount = 100.0 * (i + 1)
            orm.category = Category.FOOD
            orm.transaction_type = TransactionType.EXPENSE
            orm.source_text = f"test {i}"
            orm.id = uuid4()
            orm.occurred_at = datetime.now(timezone.utc)
            orm.description = "desc"
            orm.payment_method = "pix"
            orm.updated_at = datetime.now(timezone.utc)
            orm_objects.append(orm)
        mock_session.scalars.return_value.all.return_value = orm_objects
        params = TransactionQueryParams(limit=50)

        result = repository.find(params)

        assert len(result) == 3
        for t in result:
            assert isinstance(t, Transaction)

    def test_find_applies_limit(self, repository, mock_session):
        params = TransactionQueryParams(limit=5)
        mock_session.scalars.return_value.all.return_value = []

        repository.find(params)

        stmt = mock_session.scalars.call_args[0][0]
        assert stmt._limit == 5

    def test_find_orders_by_occurred_at_desc_by_default(self, repository, mock_session):
        params = TransactionQueryParams(limit=10)
        mock_session.scalars.return_value.all.return_value = []

        repository.find(params)

        stmt = mock_session.scalars.call_args[0][0]
        order_by_clauses = stmt._order_by_clauses
        assert any("occurred_at" in str(c) for c in order_by_clauses)


class TestAddTransaction:
    def test_add_transaction(self, repository, mock_session, sample_transaction):
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        result = repository.add_transaction(sample_transaction)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()
        assert isinstance(result, Transaction)

    def test_add_calls_session_commit_and_refresh(
        self, repository, mock_session, sample_transaction
    ):
        mock_session.add.return_value = None
        mock_session.commit.return_value = None
        mock_session.refresh.return_value = None

        repository.add_transaction(sample_transaction)

        mock_session.add.assert_called_once()
        mock_session.commit.assert_called_once()
        mock_session.refresh.assert_called_once()

    def test_add_raises_exception(self, repository, mock_session, sample_transaction):
        mock_session.add.side_effect = Exception("DB error")

        with pytest.raises(Exception, match="DB error"):
            repository.add_transaction(sample_transaction)


class TestUpdateTransaction:
    def test_update_by_id(self, repository, mock_session):
        target_id = uuid4()
        params = UpdateTransactionParams(
            id=target_id,
            match_text="target",
            date_local=date(2026, 6, 1),
            amount=200.0,
            category=Category.HEALTH,
        )
        mock_orm = MagicMock()
        mock_orm.amount = 100.0
        mock_orm.category = Category.FOOD
        mock_orm.transaction_type = TransactionType.EXPENSE
        mock_orm.source_text = "original"
        mock_orm.id = target_id
        mock_orm.occurred_at = datetime.now(timezone.utc)
        mock_orm.description = "old"
        mock_orm.payment_method = "cash"
        mock_orm.updated_at = datetime.now(timezone.utc)
        mock_session.scalar.return_value = mock_orm
        mock_session.commit.return_value = None

        result = repository.update_transaction(params)

        assert result is not None
        assert isinstance(result, Transaction)
        mock_session.commit.assert_called_once()

    def test_update_nothing_to_update(self, repository, mock_session):
        params = UpdateTransactionParams(
            match_text="teste", date_local=date(2026, 1, 1)
        )

        result = repository.update_transaction(params)

        assert result is None
        mock_session.scalar.assert_not_called()
        mock_session.commit.assert_not_called()

    def test_update_no_reference_raises(self, repository, mock_session):
        params = UpdateTransactionParams(amount=100.0)

        with pytest.raises(ValueError, match="reference"):
            repository.update_transaction(params)

    def test_update_by_match_text(self, repository, mock_session):
        params = UpdateTransactionParams(
            match_text="almoço",
            date_local=date(2026, 6, 1),
            amount=150.0,
        )
        mock_orm = MagicMock()
        mock_orm.amount = 100.0
        mock_orm.category = Category.FOOD
        mock_orm.transaction_type = TransactionType.EXPENSE
        mock_orm.source_text = "almoço"
        mock_orm.id = uuid4()
        mock_orm.occurred_at = datetime.now(timezone.utc)
        mock_orm.description = "old"
        mock_orm.payment_method = "cash"
        mock_orm.updated_at = datetime.now(timezone.utc)
        mock_session.scalar.return_value = mock_orm
        mock_session.commit.return_value = None

        result = repository.update_transaction(params)

        assert result is not None
        mock_session.commit.assert_called_once()
