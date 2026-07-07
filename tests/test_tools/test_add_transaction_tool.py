import pytest

from src.agents.financial.tools.add_transaction import AddTransactionTool
from src.model.tool_response import LegacyToolResponse
from src.model.transaction import Category, Transaction, TransactionType
from src.services.transaction_service import TransactionService


class TestAddTransactionTool:
    @pytest.fixture
    def tool(self):
        service = TransactionService.__new__(TransactionService)
        object.__setattr__(service, "_repository", None)
        return AddTransactionTool(service=service)

    def test_adds_and_returns_ok(self, tool):
        t = Transaction(
            amount=100.0,
            category=Category.FOOD,
            transaction_type=TransactionType.EXPENSE,
            source_text="test",
        )
        tool.service.add_transaction = lambda tr: tr

        result = tool._run(t)

        assert isinstance(result, LegacyToolResponse)
        assert result.status == "ok"
        assert "transaction" in result.data

    def test_handles_exception(self, tool):
        def raise_error(tr):
            raise Exception("fail")

        tool.service.add_transaction = raise_error

        t = Transaction(
            amount=100.0,
            source_text="test",
        )
        result = tool._run(t)

        assert result.status == "error"
