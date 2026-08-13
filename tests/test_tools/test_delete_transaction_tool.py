from datetime import date
from uuid import uuid4

import pytest

from app.agents.financial.tools.delete_transaction import DeleteTransactionTool
from app.model.tool_response import ToolFailure, ToolSuccess
from app.model.transaction import Category, Transaction, TransactionType
from app.model.update_transaction_params import UpdateTransactionQuery
from app.services.transaction_service import TransactionService


class TestDeleteTransactionTool:
    @pytest.fixture
    def tool(self):
        service = TransactionService.__new__(TransactionService)
        object.__setattr__(service, "_repository", None)
        return DeleteTransactionTool(service=service)

    def test_deletes_by_id_returns_true(self, tool):
        query = UpdateTransactionQuery(id=uuid4())
        updated = Transaction(
            amount=0.0,
            category=Category.OTHER,
            transaction_type=TransactionType.EXPENSE,
            source_text="cancelado",
        )
        tool.service.update_transaction = lambda p: updated

        result = tool._run(query)

        assert isinstance(result, ToolSuccess)
        assert result.data.deleted is True

    def test_no_transaction_found_returns_false(self, tool):
        query = UpdateTransactionQuery(
            match_text="inexistente",
            date_local=date(2026, 1, 1),
        )
        tool.service.update_transaction = lambda p: None

        result = tool._run(query)

        assert isinstance(result, ToolSuccess)
        assert result.data.deleted is False

    def test_handles_exception(self, tool):
        def raise_error(p):
            raise Exception("DB error")

        tool.service.update_transaction = raise_error

        query = UpdateTransactionQuery(id=uuid4())
        result = tool._run(query)

        assert isinstance(result, ToolFailure)
        assert "DB error" in result.details["exception"]
