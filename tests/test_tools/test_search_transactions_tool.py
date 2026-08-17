import pytest

from app.domain.model.transaction import Category, Transaction, TransactionType
from app.infrastructure.agents.financial.tools.search_transaction import (
    SearchTransactionsTool,
)
from app.infrastructure.agents.schema.tool_response import ToolFailure, ToolSuccess
from app.infrastructure.agents.schema.transaction import TransactionOutput
from app.infrastructure.agents.schema.transaction_query_params import (
    TransactionQueryParams,
)
from app.services.transaction_service import TransactionService


class TestSearchTransactionsTool:
    @pytest.fixture
    def tool(self):
        service = TransactionService.__new__(TransactionService)
        object.__setattr__(service, "_repository", None)
        return SearchTransactionsTool(service=service)

    def test_returns_transactions(self, tool):
        mock_result = [
            Transaction(
                amount=100.0,
                category=Category.FOOD,
                transaction_type=TransactionType.EXPENSE,
                source_text="test",
            )
        ]
        tool.service.search_transactions = lambda p: mock_result

        params = TransactionQueryParams(category=Category.FOOD)
        result = tool._run(params)

        assert isinstance(result, ToolSuccess)
        assert len(result.data.transactions) == 1

    def test_returns_empty_list(self, tool):
        tool.service.search_transactions = lambda p: []

        params = TransactionQueryParams()
        result = tool._run(params)

        assert isinstance(result, ToolSuccess)
        assert result.data.transactions == []

    def test_handles_exception(self, tool):
        def raise_error(p):
            raise Exception("fail")

        tool.service.search_transactions = raise_error

        params = TransactionQueryParams()
        result = tool._run(params)

        assert isinstance(result, ToolFailure)

    def test_transactions_are_typed_model(self, tool):
        mock_result = [
            Transaction(
                amount=50.0,
                category=Category.OTHER,
                transaction_type=TransactionType.EXPENSE,
                source_text="source",
            )
        ]
        tool.service.search_transactions = lambda p: mock_result

        params = TransactionQueryParams()
        result = tool._run(params)

        assert isinstance(result, ToolSuccess)
        assert isinstance(result.data.transactions[0], TransactionOutput)
