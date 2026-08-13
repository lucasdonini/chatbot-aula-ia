import logging

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.model.tool_response import ToolFailure, ToolResponse, ToolSuccess
from app.model.update_transaction_params import (
    UpdateTransactionParams,
    UpdateTransactionQuery,
)
from app.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)


class _DeleteTransactionArgsSchema(BaseModel):
    query: UpdateTransactionQuery


class _DeleteTransactionResponse(BaseModel):
    deleted: bool


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

    def _run(
        self, query: UpdateTransactionQuery
    ) -> ToolResponse[_DeleteTransactionResponse]:
        logger.debug(
            "Tool called",
            extra={"details": {"tool": self.name, "query": query.model_dump()}},
        )
        params = UpdateTransactionParams(query=query, is_canceled=True)
        response: _DeleteTransactionResponse
        try:
            if self.service.update_transaction(params):
                logger.debug(
                    "Tool succeeded",
                    extra={"details": {"tool": self.name, "deleted": True}},
                )
                response = _DeleteTransactionResponse(deleted=True)
            else:
                logger.debug(
                    "Tool succeeded",
                    extra={"details": {"tool": self.name, "deleted": False}},
                )
                response = _DeleteTransactionResponse(deleted=False)
            return ToolSuccess(data=response)
        except Exception as e:
            logger.exception(
                "Tool failed",
                extra={"details": {"tool": self.name}},
            )
            return ToolFailure.exception(e)
