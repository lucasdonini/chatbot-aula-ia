import logging

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.model.tool_response import ToolResponse
from src.model.update_transaction_params import (
    UpdateTransactionParams,
    UpdateTransactionQuery,
)
from src.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)


class _DeleteTransactionArgsSchema(BaseModel):
    query: UpdateTransactionQuery


TOOL_NAME = "delete_transaction"


class DeleteTransactionTool(BaseTool):
    name: str = TOOL_NAME
    args_schema: type[BaseModel] = _DeleteTransactionArgsSchema
    description: str = (
        "Deleta / cancela uma transação existente.\n"
        "Estratégias:\n"
        "\t- Se 'id' for informado: deleta diretamente por ID.\n"
        "\t- Caso contrário: localiza a transação mais recente que combine "
        "(match_text em source_text/description) "
        "E (date_local em America/Sao_Paulo), então deleta.\n"
        "Retorna verdadeiro se deletou algo, falso caso contrário"
    )

    service: TransactionService = Field(exclude=True)

    def _run(self, query: UpdateTransactionQuery) -> ToolResponse:
        logger.debug(
            "Tool called",
            extra={"details": {"tool": self.name, "query": query.model_dump()}},
        )
        params = UpdateTransactionParams(query=query, is_canceled=True)
        try:
            if self.service.update_transaction(params):
                logger.debug(
                    "Tool succeeded",
                    extra={"details": {"tool": self.name, "deleted": True}},
                )
                return ToolResponse.ok({"deleted": True})
            else:
                logger.debug(
                    "Tool succeeded",
                    extra={"details": {"tool": self.name, "deleted": False}},
                )
                return ToolResponse.ok({"deleted": False})
        except Exception as e:
            logger.exception(
                "Tool failed",
                extra={"details": {"tool": self.name}},
            )
            return ToolResponse.exception(e)
