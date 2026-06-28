import logging

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.model.tool_response import ToolResponse
from src.model.update_transaction_params import UpdateTransactionParams
from src.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)


class UpdateTransactionTool(BaseTool):
    name: str = "update_transaction"
    args_schema: type[BaseModel] = UpdateTransactionParams
    description: str = """
Atualiza uma transação existente.
Estratégias:
    - Se 'id' for informado: atualiza diretamente por ID.
    - Caso contrário: localiza a transação mais recente que combine
        (match_text em source_text/description)
        E (date_local em America/Sao_Paulo), então atualiza.
Retorna o registro atualizado.
"""

    service: TransactionService = Field(exclude=True)

    def _run(self, *args, **kwargs) -> ToolResponse:
        params = args[0] if args else UpdateTransactionParams(**kwargs)
        logger.info("%s tool called. params %s", self.name, params)
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
