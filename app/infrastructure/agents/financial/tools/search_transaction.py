import logging

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.application.models.transaction_query import (
    TransactionQueryParams,
)
from app.infrastructure.agents.financial.schemas.tool_response import (
    ToolFailure,
    ToolResponse,
    ToolSuccess,
)
from app.infrastructure.agents.financial.schemas.transaction import TransactionOutput
from app.services.transaction_service import TransactionService

logger = logging.getLogger(__name__)


class _SearchTransactionsArgsSchema(BaseModel):
    params: TransactionQueryParams


class _SearchTransactionsResponse(BaseModel):
    transactions: list[TransactionOutput]


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

    def _run(
        self, params: TransactionQueryParams
    ) -> ToolResponse[_SearchTransactionsResponse]:
        raise NotImplementedError("This tool only supports asynchronous execution")

    async def _arun(
        self, params: TransactionQueryParams
    ) -> ToolResponse[_SearchTransactionsResponse]:
        logger.debug(
            "Tool called",
            extra={"details": {"tool": self.name, "params": params.model_dump()}},
        )
        try:
            result = await self.service.search_transactions(params)
            logger.debug(
                "Tool succeeded",
                extra={"details": {"tool": self.name, "count": len(result)}},
            )
            return ToolSuccess(
                data=_SearchTransactionsResponse(
                    transactions=[
                        TransactionOutput.from_domain(item) for item in result
                    ]
                )
            )
        except Exception as e:
            logger.exception(
                "Tool failed",
                extra={"details": {"tool": self.name}},
            )
            return ToolFailure.exception(e)
