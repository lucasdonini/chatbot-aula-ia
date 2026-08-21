import logging

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.application.models.transaction_update import (
    UpdateTransactionParams,
    UpdateTransactionQuery,
)
from app.infrastructure.agents.financial.schemas.tool_response import (
    ToolFailure,
    ToolResponse,
    ToolSuccess,
)
from app.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)


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

    def _run(
        self, query: UpdateTransactionQuery
    ) -> ToolResponse[_RestoreTransactionResponse]:
        logger.debug(
            "Tool called",
            extra={"details": {"tool": self.name, "query": query.model_dump()}},
        )
        params = UpdateTransactionParams(query=query, is_canceled=False)
        response: _RestoreTransactionResponse
        try:
            if self.service.update_transaction(params):
                logger.debug(
                    "Tool succeeded",
                    extra={"details": {"tool": self.name, "restored": True}},
                )
                response = _RestoreTransactionResponse(restored=True)
            else:
                logger.debug(
                    "Tool succeeded",
                    extra={"details": {"tool": self.name, "restored": False}},
                )
                response = _RestoreTransactionResponse(restored=False)
            return ToolSuccess(data=response)
        except Exception as e:
            logger.exception(
                "Tool failed",
                extra={"details": {"tool": self.name}},
            )
            return ToolFailure.exception(e)
