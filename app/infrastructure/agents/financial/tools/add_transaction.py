import logging

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.infrastructure.agents.financial.schemas.tool_response import (
    ToolFailure,
    ToolResponse,
    ToolSuccess,
)
from app.infrastructure.agents.financial.schemas.transaction import (
    TransactionInput,
    TransactionOutput,
)
from app.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)


class _AddTransactionArgsSchema(BaseModel):
    transaction: TransactionInput


class _AddTransactionResponse(BaseModel):
    transaction: TransactionOutput


TOOL_NAME = "add_transaction"


class AddTransactionTool(BaseTool):
    name: str = TOOL_NAME
    args_schema: type[BaseModel] = _AddTransactionArgsSchema
    description: str = "Insere uma transação financeira no banco de dados PosthreSQL."

    service: TransactionService = Field(exclude=True)

    def _run(
        self, transaction: TransactionInput
    ) -> ToolResponse[_AddTransactionResponse]:
        raise NotImplementedError("This tool only supports asynchronous execution")

    async def _arun(
        self, transaction: TransactionInput
    ) -> ToolResponse[_AddTransactionResponse]:
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
            added = await self.service.add_transaction(transaction.to_domain())
            logger.debug(
                "Tool succeeded",
                extra={"details": {"tool": self.name, "added": added}},
            )
            return ToolSuccess(
                data=_AddTransactionResponse(
                    transaction=TransactionOutput.from_domain(added)
                )
            )
        except Exception as e:
            logger.exception(
                "Tool failed",
                extra={"details": {"tool": self.name}},
            )
            return ToolFailure.exception(e)
