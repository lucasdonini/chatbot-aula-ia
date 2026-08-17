from datetime import date
from uuid import uuid4

import pytest

from app.infrastructure.agents.financial.tools.update_transaction import (
    UpdateTransactionTool,
)
from app.infrastructure.agents.schema.tool_response import ToolFailure, ToolSuccess
from app.infrastructure.agents.schema.update_transaction_params import (
    UpdateTransactionParams,
    UpdateTransactionQuery,
)
from app.model.transaction import Category, Transaction, TransactionType
from app.services.transaction_service import TransactionService


class TestUpdateTransactionTool:
    @pytest.fixture
    def tool(self):
        service = TransactionService.__new__(TransactionService)
        object.__setattr__(service, "_repository", None)
        return UpdateTransactionTool(service=service)

    def test_updates_and_returns_ok(self, tool):
        params = UpdateTransactionParams(
            query=UpdateTransactionQuery(id=uuid4()),
            amount=200.0,
            category=Category.FOOD,
        )
        updated = Transaction(
            amount=200.0,
            category=Category.FOOD,
            transaction_type=TransactionType.EXPENSE,
            source_text="original",
        )
        tool.service.update_transaction = lambda p: updated

        result = tool._run(params)

        assert isinstance(result, ToolSuccess)
        assert result.data.updated is not None
        assert result.data.updated.amount == 200.0

    def test_nothing_to_update(self, tool):
        params = UpdateTransactionParams(
            query=UpdateTransactionQuery(
                match_text="teste", date_local=date(2026, 1, 1)
            ),
        )
        tool.service.update_transaction = lambda p: None

        result = tool._run(params)

        assert isinstance(result, ToolSuccess)
        assert result.data.updated is None

    def test_handles_exception(self, tool):
        def raise_error(p):
            raise Exception("fail")

        tool.service.update_transaction = raise_error

        params = UpdateTransactionParams(
            query=UpdateTransactionQuery(id=uuid4()),
            amount=200.0,
        )
        result = tool._run(params)

        assert isinstance(result, ToolFailure)
