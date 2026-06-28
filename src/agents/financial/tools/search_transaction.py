import logging

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from model.transaction_query_params import TransactionQueryParams
from src.model.tool_response import ToolResponse
from src.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)


class SearchTransactionsTool(BaseTool):
    name: str = "search_transactions"
    args_schema: type[BaseModel] = TransactionQueryParams
    description: str = (
        "Busca no banco de dados uma transação de acordo com os parâmetros passados. "
        "Caso nenhum parâmetro seja passado, retorna as útlimas 10 transações. "
        "Se a data de início for passada mas a de final não, retorna todas desde o "
        "início até hoje. "
        "Se a data de início não for passada mas a de final for, retora todas até a "
        "data de final. "
        "Buscar usando parâmetros como source_text e description pode ser ineficiente, "
        "uma vez que são textos humanos, o que os torna menos padronizados. "
        "Buscas por source_text ou description fazem busca parcial para permitir "
        "que transações com description "
        "'fiz uma doação para ...' sejam retornadas buscando apenas por 'doação'."
    )

    service: TransactionService = Field(exclude=True)

    def _run(self, params: TransactionQueryParams, *args, **kwargs) -> ToolResponse:
        logger.info("%s tool called. Params: %s", self.name, params)
        try:
            result = self.service.search_transactions(params)
            logger.debug(
                "%s tool searched a total of %s transactions", self.name, len(result)
            )
            return ToolResponse.ok({"transactions": [t.model_dump() for t in result]})
        except Exception as e:
            logger.exception("Exception raised while searching transactions")
            return ToolResponse.exception(e)
