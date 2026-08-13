import logging

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.model.tool_response import ToolFailure, ToolResponse, ToolSuccess
from app.model.transaction import Transaction
from app.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)


class _AddTransactionArgsSchema(BaseModel):
    transaction: Transaction


class _AddTransactionResponse(BaseModel):
    transaction: Transaction


TOOL_NAME = "add_transaction"


class AddTransactionTool(BaseTool):
    name: str = TOOL_NAME
    args_schema: type[BaseModel] = _AddTransactionArgsSchema
    description: str = "Insere uma transação financeira no banco de dados PosthreSQL."

    service: TransactionService = Field(exclude=True)

    def _run(self, transaction: Transaction) -> ToolResponse[_AddTransactionResponse]:
        logger.debug(
            "Tool called",
            extra={
                "details": {
                    "tool": self.name,
                    "transaction": transaction.model_dump(),
                }
            },
        )
        try:
            added = self.service.add_transaction(transaction)
            logger.debug(
                "Tool succeeded",
                extra={"details": {"tool": self.name, "added": added.model_dump()}},
            )
            return ToolSuccess(data=_AddTransactionResponse(transaction=added))
        except Exception as e:
            logger.exception(
                "Tool failed",
                extra={"details": {"tool": self.name}},
            )
            return ToolFailure.exception(e)
