from datetime import date
from uuid import uuid4

import pytest

from src.agents.financial.tools.update_transaction import UpdateTransactionTool
from src.model.tool_response import ToolResponse
from src.model.transaction import Category, Transaction, TransactionType
from src.model.update_transaction_params import UpdateTransactionParams
from src.services.transaction_service import TransactionService


class TestUpdateTransactionTool:
    @pytest.fixture
    def tool(self):
        service = TransactionService.__new__(TransactionService)
        object.__setattr__(service, "_repository", None)
        return UpdateTransactionTool(service=service)

    def test_updates_and_returns_ok(self, tool):
        params = UpdateTransactionParams(
            id=uuid4(), amount=200.0, category=Category.FOOD
        )
        updated = Transaction(
            amount=200.0,
            category=Category.FOOD,
            transaction_type=TransactionType.EXPENSE,
            source_text="original",
        )
        tool.service.update_transaction = lambda p: updated

        result = tool._run(params)

        assert isinstance(result, ToolResponse)
        assert result.status == "ok"
        assert "updated" in result.data

    def test_nothing_to_update(self, tool):
        params = UpdateTransactionParams(
            match_text="teste", date_local=date(2026, 1, 1)
        )
        tool.service.update_transaction = lambda p: None

        result = tool._run(params)

        assert result.status == "ok"
        assert result.data["updated"] == "Nothing to update"

    def test_handles_exception(self, tool):
        def raise_error(p):
            raise Exception("fail")

        tool.service.update_transaction = raise_error

        params = UpdateTransactionParams(id=uuid4(), amount=200.0)
        result = tool._run(params)

        assert result.status == "error"
