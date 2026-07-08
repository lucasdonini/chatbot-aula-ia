import logging

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.model.tool_response import ToolFailure, ToolResponse, ToolSuccess
from src.model.transaction import Transaction
from src.model.update_transaction_params import UpdateTransactionParams
from src.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)


class _UpdateTransactionArgsSchema(BaseModel):
    params: UpdateTransactionParams


class _UpdateTransactionResponse(BaseModel):
    updated: Transaction | None = None


TOOL_NAME = "update_transaction"


class UpdateTransactionTool(BaseTool):
    name: str = TOOL_NAME
    args_schema: type[BaseModel] = _UpdateTransactionArgsSchema
    description: str = (
        "Atualiza uma transação existente.\n"
        "Estratégias:\n"
        "\t- Se 'id' for informado: atualiza diretamente por ID.\n"
        "\t- Caso contrário: localiza a transação mais recente que combine "
        "(match_text em source_text/description) "
        "E (date_local em America/Sao_Paulo), então atualiza.\n"
        "Retorna o registro atualizado."
    )

    service: TransactionService = Field(exclude=True)

    def _run(
        self, params: UpdateTransactionParams
    ) -> ToolResponse[_UpdateTransactionResponse]:
        logger.debug(
            "Tool called",
            extra={"details": {"tool": self.name, "params": params.model_dump()}},
        )
        try:
            if updated := self.service.update_transaction(params):
                logger.debug(
                    "Tool succeeded",
                    extra={
                        "details": {
                            "tool": self.name,
                            "updated": updated.model_dump(),
                        }
                    },
                )
                return ToolSuccess(data=_UpdateTransactionResponse(updated=updated))
            else:
                logger.debug(
                    "Tool succeeded",
                    extra={"details": {"tool": self.name, "updated": None}},
                )
                return ToolSuccess(data=_UpdateTransactionResponse())
        except Exception as e:
            logger.exception(
                "Tool failed",
                extra={"details": {"tool": self.name}},
            )
            return ToolFailure.exception(e)
