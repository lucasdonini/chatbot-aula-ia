from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.application.ports.logger import Logger
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
    logger: Logger = Field(exclude=True)

    def _run(
        self, transaction: TransactionInput
    ) -> ToolResponse[_AddTransactionResponse]:
        raise NotImplementedError("This tool only supports asynchronous execution")

    async def _arun(
        self, transaction: TransactionInput
    ) -> ToolResponse[_AddTransactionResponse]:
        self.logger.debug(
            "Tool called",
            details={
                "tool": self.name,
                "category": transaction.category.value,
                "transaction_type": transaction.transaction_type.value,
            },
        )
        try:
            added = await self.service.add_transaction(transaction.to_domain())
            self.logger.debug(
                "Tool succeeded",
                details={"tool": self.name, "added": True},
            )
            return ToolSuccess(
                data=_AddTransactionResponse(
                    transaction=TransactionOutput.from_domain(added)
                )
            )
        except Exception as e:
            self.logger.exception(
                "Tool failed",
                exception=e,
                details={"tool": self.name},
            )
            return ToolFailure.exception(e)
