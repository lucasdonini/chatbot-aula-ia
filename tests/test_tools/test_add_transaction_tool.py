import pytest

from app.domain.model.transaction import Category, TransactionType
from app.infrastructure.agents.financial.tools.add_transaction import AddTransactionTool
from app.infrastructure.agents.schema.tool_response import ToolFailure, ToolSuccess
from app.infrastructure.agents.schema.transaction import (
    TransactionInput,
    TransactionOutput,
)
from app.services.transaction_service import TransactionService


class TestAddTransactionTool:
    @pytest.fixture
    def tool(self):
        service = TransactionService.__new__(TransactionService)
        object.__setattr__(service, "_repository", None)
        return AddTransactionTool(service=service)

    def test_adds_and_returns_ok(self, tool):
        t = TransactionInput(
            amount=100.0,
            category=Category.FOOD,
            transaction_type=TransactionType.EXPENSE,
            source_text="test",
        )
        tool.service.add_transaction = lambda tr: tr

        result = tool._run(t)

        assert isinstance(result, ToolSuccess)
        assert result.data.transaction is not None
        assert result.data.transaction.amount == 100.0
        assert isinstance(result.data.transaction, TransactionOutput)

    def test_handles_exception(self, tool):
        def raise_error(tr):
            raise Exception("fail")

        tool.service.add_transaction = raise_error

        t = TransactionInput(
            amount=100.0,
            source_text="test",
        )
        result = tool._run(t)

        assert isinstance(result, ToolFailure)
