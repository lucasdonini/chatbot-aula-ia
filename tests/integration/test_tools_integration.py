from datetime import date

import pytest

from src.agents.financial.tools.add_transaction import AddTransactionTool
from src.agents.financial.tools.daily_balance import DailyBalanceTool
from src.agents.financial.tools.search_transaction import SearchTransactionsTool
from src.agents.financial.tools.total_balance import TotalBalanceTool
from src.agents.financial.tools.update_transaction import UpdateTransactionTool
from src.model.transaction import Category, Transaction, TransactionType
from src.model.transaction_query_params import TransactionQueryParams
from src.model.update_transaction_params import UpdateTransactionParams

pytestmark = [
    pytest.mark.usefixtures("apply_migrations"),
]


@pytest.fixture
def total_balance_tool(transaction_service):
    return TotalBalanceTool(service=transaction_service)


@pytest.fixture
def daily_balance_tool(transaction_service):
    return DailyBalanceTool(service=transaction_service)


@pytest.fixture
def search_tool(transaction_service):
    return SearchTransactionsTool(service=transaction_service)


@pytest.fixture
def add_tool(transaction_service):
    return AddTransactionTool(service=transaction_service)


@pytest.fixture
def update_tool(transaction_service):
    return UpdateTransactionTool(service=transaction_service)


class TestTotalBalanceTool:
    def test_returns_balance(self, total_balance_tool, seed_transactions):
        result = total_balance_tool._run()
        assert result.status == "ok"
        assert result.data["saldo"] == 7600.00

    def test_empty_db_returns_zero(self, total_balance_tool, db_session):
        result = total_balance_tool._run()
        assert result.status == "ok"
        assert result.data["saldo"] == 0.0


class TestDailyBalanceTool:
    def test_returns_daily_balance(self, daily_balance_tool, seed_transactions):
        result = daily_balance_tool._run(target_date=date(2026, 6, 1))
        assert result.status == "ok"
        assert result.data["saldo_diario"] == 4850.00

    def test_no_transactions_on_date(self, daily_balance_tool, db_session):
        result = daily_balance_tool._run(target_date=date(2025, 1, 1))
        assert result.status == "ok"
        assert result.data["saldo_diario"] == 0.0


class TestSearchTransactionsTool:
    def test_search_by_category(self, search_tool, seed_transactions):
        params = TransactionQueryParams(category=Category.FOOD, limit=50)
        result = search_tool._run(params)
        assert result.status == "ok"
        assert len(result.data["transactions"]) >= 1

    def test_no_results(self, search_tool, seed_transactions):
        params = TransactionQueryParams(source_text="xyz_nonexistent", limit=50)
        result = search_tool._run(params)
        assert result.status == "ok"
        assert result.data["transactions"] == []

    def test_returns_dicts(self, search_tool, seed_transactions):
        params = TransactionQueryParams(limit=1)
        result = search_tool._run(params)
        assert isinstance(result.data["transactions"][0], dict)


class TestAddTransactionTool:
    def test_add_transaction(self, add_tool, db_session):
        t = Transaction(
            amount=99.00,
            category=Category.GIFTS,
            transaction_type=TransactionType.EXPENSE,
            description="Presente",
            source_text="Comprei presente",
        )
        result = add_tool._run(t)
        assert result.status == "ok"
        assert "transaction" in result.data

    def test_add_and_verify(self, add_tool, transaction_service, db_session):
        t = Transaction(
            amount=50.00,
            source_text="teste add tool",
        )
        add_result = add_tool._run(t)
        assert add_result.status == "ok"

        params = TransactionQueryParams(source_text="teste add tool", limit=50)
        search_result = transaction_service.search_transactions(params)
        assert len(search_result) >= 1


class TestUpdateTransactionTool:
    def test_update_by_id(self, update_tool, seed_transactions):
        target = seed_transactions[0]
        params = UpdateTransactionParams(
            id=target.id,
            match_text="target",
            date_local=date(2026, 6, 1),
            amount=6000.00,
            description="Atualizado via tool",
        )
        result = update_tool._run(params)
        assert result.status == "ok"
        assert "updated" in result.data

    def test_nothing_to_update(self, update_tool, seed_transactions):
        params = UpdateTransactionParams(
            match_text="almoço",
            date_local=date(2026, 6, 1),
        )
        result = update_tool._run(params)
        assert result.status == "ok"
        assert result.data["updated"] == "Nothing to update"
