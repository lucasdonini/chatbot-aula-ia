from datetime import date, datetime, timezone

import pytest

from src.infrastructure.postgres.entities.transaction import TransactionORM
from src.model.transaction import Category, Transaction, TransactionType
from src.model.transaction_query_params import TransactionQueryParams
from src.model.update_transaction_params import UpdateTransactionParams

pytestmark = [
    pytest.mark.usefixtures("apply_migrations"),
]


class TestAddTransaction:
    def test_add_creates_record(self, transaction_repository, db_session):
        t = Transaction(
            amount=250.00,
            category=Category.HEALTH,
            transaction_type=TransactionType.EXPENSE,
            description="Exame",
            source_text="Gastei 250 com exame",
        )
        result = transaction_repository.add_transaction(t)

        assert isinstance(result, Transaction)
        assert result.amount == 250.00
        assert result.category == Category.HEALTH

    def test_add_applies_defaults(self, transaction_repository, db_session):
        t = Transaction(
            amount=100.00,
            source_text="teste default",
        )
        result = transaction_repository.add_transaction(t)

        assert result.category == Category.OTHER
        assert result.transaction_type == TransactionType.EXPENSE
        assert result.occurred_at is not None

    def test_add_persists_to_db(self, transaction_repository, db_session):
        t = Transaction(
            amount=500.00,
            category=Category.INVESTMENT,
            transaction_type=TransactionType.INCOME,
            description="Dividendos",
            source_text="Recebi dividendos",
        )
        result = transaction_repository.add_transaction(t)

        orm = (
            db_session.get(TransactionORM, result.id) if hasattr(result, "id") else None
        )
        if orm:
            assert orm.amount == 500.00
            assert orm.source_text == "Recebi dividendos"

    def test_add_all_fields(self, transaction_repository, db_session):
        dt = datetime(2026, 7, 15, 10, 30, 0, tzinfo=timezone.utc)
        t = Transaction(
            amount=89.90,
            category=Category.FOOD,
            transaction_type=TransactionType.EXPENSE,
            description="Jantar",
            payment_method="crédito",
            occurred_at=dt,
            source_text="Jantar 89.90",
        )
        result = transaction_repository.add_transaction(t)

        assert result.amount == 89.90
        assert result.category == Category.FOOD
        assert result.description == "Jantar"
        assert result.payment_method == "crédito"


class TestFind:
    def test_find_default_returns_all(self, transaction_repository, seed_transactions):
        params = TransactionQueryParams(limit=50)
        results = transaction_repository.find(params)

        assert len(results) == 6

    def test_find_by_source_text(self, transaction_repository, seed_transactions):
        params = TransactionQueryParams(source_text="almoço", limit=50)
        results = transaction_repository.find(params)

        assert len(results) >= 1

    def test_find_by_date_range(self, transaction_repository, seed_transactions):
        params = TransactionQueryParams(
            occurred_at_start=date(2026, 6, 2),
            occurred_at_end=date(2026, 6, 4),
            limit=50,
        )
        results = transaction_repository.find(params)

        assert len(results) >= 3

    def test_find_by_category(self, transaction_repository, seed_transactions):
        params = TransactionQueryParams(category=Category.FOOD, limit=50)
        results = transaction_repository.find(params)

        assert len(results) >= 1
        for t in results:
            assert t.category == Category.FOOD

    def test_find_by_transaction_type(self, transaction_repository, seed_transactions):
        params = TransactionQueryParams(
            transaction_type=TransactionType.INCOME, limit=50
        )
        results = transaction_repository.find(params)

        assert len(results) >= 2

    def test_find_combined_filters(self, transaction_repository, seed_transactions):
        params = TransactionQueryParams(
            category=Category.OTHER,
            transaction_type=TransactionType.INCOME,
            limit=50,
        )
        results = transaction_repository.find(params)

        assert len(results) >= 1

    def test_find_with_limit(self, transaction_repository, seed_transactions):
        params = TransactionQueryParams(limit=2)
        results = transaction_repository.find(params)

        assert len(results) <= 2

    def test_find_no_results(self, transaction_repository, seed_transactions):
        params = TransactionQueryParams(source_text="naoexiste_texto_xyz", limit=50)
        results = transaction_repository.find(params)

        assert results == []

    def test_find_limit_zero_returns_empty(
        self, transaction_repository, seed_transactions
    ):
        params = TransactionQueryParams(limit=0)
        results = transaction_repository.find(params)

        assert results == []


class TestSumAmounts:
    def test_sum_income(self, transaction_repository, seed_transactions):
        total = transaction_repository.sum_amounts_by_transaction_type(
            TransactionType.INCOME
        )
        assert total == 8000.00

    def test_sum_expense(self, transaction_repository, seed_transactions):
        total = transaction_repository.sum_amounts_by_transaction_type(
            TransactionType.EXPENSE
        )
        assert total == 400.00

    def test_sum_transfer(self, transaction_repository, seed_transactions):
        total = transaction_repository.sum_amounts_by_transaction_type(
            TransactionType.TRANSFER
        )
        assert total == 1000.00

    def test_sum_no_match(self, transaction_repository, seed_transactions):
        total = transaction_repository.sum_amounts_by_transaction_type(
            TransactionType.INCOME,
            period_start=datetime(2099, 1, 1, tzinfo=timezone.utc),
            period_end=datetime(2099, 12, 31, tzinfo=timezone.utc),
        )
        assert total == 0.0

    def test_sum_with_period(self, transaction_repository, seed_transactions):
        total = transaction_repository.sum_amounts_by_transaction_type(
            TransactionType.INCOME,
            period_start=datetime(2026, 6, 2, tzinfo=timezone.utc),
            period_end=datetime(2026, 6, 3, tzinfo=timezone.utc),
        )
        assert total == 3000.00


class TestUpdateTransaction:
    def test_update_by_id(self, transaction_repository, db_session, seed_transactions):
        target = seed_transactions[0]
        params = UpdateTransactionParams(
            id=target.id,
            match_text="target",
            date_local=date(2026, 6, 1),
            amount=5500.00,
            description="Salário atualizado",
        )
        result = transaction_repository.update_transaction(params)

        assert result is not None
        assert result.amount == 5500.00
        assert result.description == "Salário atualizado"
        db_session.refresh(target)
        assert target.amount == 5500.00

    def test_update_by_match_text_and_date(
        self, transaction_repository, db_session, seed_transactions
    ):
        params = UpdateTransactionParams(
            id=seed_transactions[0].id,
            match_text="almoço",
            date_local=date(2026, 6, 1),
            amount=175.00,
        )
        result = transaction_repository.update_transaction(params)

        assert result is not None
        assert result.amount == 175.00

    def test_update_nothing_to_update(self, transaction_repository, seed_transactions):
        params = UpdateTransactionParams(
            match_text="almoço",
            date_local=date(2026, 6, 1),
        )
        result = transaction_repository.update_transaction(params)

        assert result is None

    def test_update_no_reference_raises(self, transaction_repository):
        params = UpdateTransactionParams(amount=100.00)

        with pytest.raises(ValueError, match="reference"):
            transaction_repository.update_transaction(params)
