from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.application.models.transaction_update import (
    UpdateTransactionParams,
    UpdateTransactionQuery,
)
from app.application.ports.logger import Logger
from app.infrastructure.agents.financial.schemas.tool_response import (
    ToolFailure,
    ToolResponse,
    ToolSuccess,
)
from app.services.transaction_service import TransactionService


class _RestoreTransactionArgsSchema(BaseModel):
    query: UpdateTransactionQuery


class _RestoreTransactionResponse(BaseModel):
    restored: bool


TOOL_NAME = "restore_transaction"


class RestoreTransactionTool(BaseTool):
    name: str = TOOL_NAME
    args_schema: type[BaseModel] = _RestoreTransactionArgsSchema
    description: str = (
        "Restaura uma transação deletada / cancelada.\n"
        "Estratégias:\n"
        "\t- Se 'id' for informado: restaura diretamente por ID.\n"
        "\t- Caso contrário: localiza a transação mais recente que combine "
        "(match_text em source_text/description) "
        "E (date_local em America/Sao_Paulo), então restaura.\n"
        "Retorna verdadeiro se restaurou algo, falso caso contrário"
    )

    service: TransactionService = Field(exclude=True)
    logger: Logger = Field(exclude=True)

    def _run(
        self, query: UpdateTransactionQuery
    ) -> ToolResponse[_RestoreTransactionResponse]:
        raise NotImplementedError("This tool only supports asynchronous execution")

    async def _arun(
        self, query: UpdateTransactionQuery
    ) -> ToolResponse[_RestoreTransactionResponse]:
        self.logger.debug(
            "Tool called",
            details={
                "tool": self.name,
                "lookup_fields": sorted(
                    key
                    for key, value in query.model_dump().items()
                    if value is not None
                ),
            },
        )
        params = UpdateTransactionParams(query=query, is_canceled=False)
        response: _RestoreTransactionResponse
        try:
            if await self.service.update_transaction(params):
                self.logger.debug(
                    "Tool succeeded",
                    details={"tool": self.name, "restored": True},
                )
                response = _RestoreTransactionResponse(restored=True)
            else:
                self.logger.debug(
                    "Tool succeeded",
                    details={"tool": self.name, "restored": False},
                )
                response = _RestoreTransactionResponse(restored=False)
            return ToolSuccess(data=response)
        except Exception as e:
            self.logger.exception(
                "Tool failed",
                exception=e,
                details={"tool": self.name},
            )
            return ToolFailure.exception(e)
