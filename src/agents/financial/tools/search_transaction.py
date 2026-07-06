import logging

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.model.tool_response import ToolResponse
from src.model.transaction_query_params import TransactionQueryParams
from src.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)


class _SearchTransactionsArgsSchema(BaseModel):
    params: TransactionQueryParams


TOOL_NAME = "search_transactions"


class SearchTransactionsTool(BaseTool):
    name: str = TOOL_NAME
    args_schema: type[BaseModel] = _SearchTransactionsArgsSchema
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

    def _run(self, params: TransactionQueryParams) -> ToolResponse:
        logger.debug(
            "Tool called",
            extra={"details": {"tool": self.name, "params": params.model_dump()}},
        )
        try:
            result = self.service.search_transactions(params)
            logger.debug(
                "Tool succeeded",
                extra={"details": {"tool": self.name, "count": len(result)}},
            )
            return ToolResponse.ok({"transactions": [t.model_dump() for t in result]})
        except Exception as e:
            logger.exception(
                "Tool failed",
                extra={"details": {"tool": self.name}},
            )
            return ToolResponse.exception(e)
