from datetime import date

import pytest

from app.application.models.transaction_query import (
    TransactionQueryParams,
)
from app.application.models.transaction_update import (
    UpdateTransactionParams,
    UpdateTransactionQuery,
)
from app.domain.model.transaction import Category, Transaction, TransactionType

pytestmark = [
    pytest.mark.integration,
    pytest.mark.asyncio,
    pytest.mark.usefixtures("apply_migrations"),
]


class TestCalculateTotalBalance:
    async def test_positive_balance(self, transaction_service, seed_transactions):
        balance = await transaction_service.calculate_total_balance()
        # INCOME(5000+3000) - EXPENSE(150+50+200) = 8000 - 400 = 7600
        assert balance == 7600.00

    async def test_zero_balance_no_transactions(
        self, transaction_repository, db_session
    ):
        from app.services.transaction_service import TransactionService

        service = TransactionService(repository=transaction_repository)
        balance = await service.calculate_total_balance()
        assert balance == 0.0


class TestCalculateDailyBalance:
    async def test_daily_balance(self, transaction_service, seed_transactions):
        balance = await transaction_service.calculate_daily_balance(date(2026, 6, 1))
        # INCOME(5000) - EXPENSE(150) = 4850
        assert balance == 4850.00

    async def test_daily_balance_another_day(
        self, transaction_service, seed_transactions
    ):
        balance = await transaction_service.calculate_daily_balance(date(2026, 6, 2))
        # Acumulado até 02/06: INCOME(5000+3000) - EXPENSE(150+50) = 7800
        assert balance == 7800.00

    async def test_daily_balance_no_transactions(
        self, transaction_repository, db_session
    ):
        from app.services.transaction_service import TransactionService

        service = TransactionService(repository=transaction_repository)
        balance = await service.calculate_daily_balance(date(2026, 1, 1))
        assert balance == 0.0


class TestSearchTransactions:
    async def test_search_by_category(self, transaction_service, seed_transactions):
        params = TransactionQueryParams(category=Category.HEALTH, limit=50)
        results = await transaction_service.search_transactions(params)
        assert len(results) >= 1
        for t in results:
            assert t.category == Category.HEALTH

    async def test_search_all(self, transaction_service, seed_transactions):
        params = TransactionQueryParams(limit=50)
        results = await transaction_service.search_transactions(params)
        assert len(results) == 6


class TestAddTransaction:
    async def test_add_and_retrieve(self, transaction_service, db_session):
        t = Transaction(
            amount=300.00,
            category=Category.BILLS,
            transaction_type=TransactionType.EXPENSE,
            description="Conta de luz",
            source_text="Paguei conta de luz",
        )
        result = await transaction_service.add_transaction(t)

        assert result.amount == 300.00
        assert result.category == Category.BILLS


class TestUpdateTransaction:
    async def test_update(self, transaction_service, seed_transactions):
        target = seed_transactions[0]
        params = UpdateTransactionParams(
            query=UpdateTransactionQuery(id=target.id),
            amount=5200.00,
        )
        result = await transaction_service.update_transaction(params)

        assert result is not None
        assert result.amount == 5200.00

    async def test_update_no_match(self, transaction_service, seed_transactions):
        params = UpdateTransactionParams(
            query=UpdateTransactionQuery(
                match_text="inexistente",
                date_local=date(2026, 6, 1),
            ),
        )
        assert params.has_update is False
        result = await transaction_service.update_transaction(params)
        assert result is None

    async def test_update_no_reference(self, transaction_service):
        params = UpdateTransactionParams(
            query=UpdateTransactionQuery(),
            amount=100.00,
        )
        with pytest.raises(ValueError):
            await transaction_service.update_transaction(params)
