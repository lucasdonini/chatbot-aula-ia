import logging

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.model.tool_response import ToolResponse
from src.model.update_transaction_params import UpdateTransactionParams
from src.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)


class _UpdateTransactionArgsSchema(BaseModel):
    params: UpdateTransactionParams


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

    def _run(self, params: UpdateTransactionParams) -> ToolResponse:
        logger.debug("%s tool called. params %s", self.name, params)
        try:
            if updated := self.service.update_transaction(params):
                logger.debug("Transcation updated successfully")
                return ToolResponse.ok({"updated": updated})
            else:
                logger.debug("No transaction updated.")
                return ToolResponse.ok({"updated": "Nothing to update"})
        except Exception as e:
            logger.exception("Exception rasied while updating transaction")
            return ToolResponse.exception(e)
