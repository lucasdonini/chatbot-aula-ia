from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.application.exceptions import ApplicationError
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
    logger: Logger = Field(exclude=True)

    def _run(
        self, query: UpdateTransactionQuery
    ) -> ToolResponse[_DeleteTransactionResponse]:
        raise NotImplementedError("This tool only supports asynchronous execution")

    async def _arun(
        self, query: UpdateTransactionQuery
    ) -> ToolResponse[_DeleteTransactionResponse]:
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
        params = UpdateTransactionParams(query=query, is_canceled=True)
        response: _DeleteTransactionResponse
        try:
            await self.service.update_transaction(params)
            self.logger.debug(
                "Tool succeeded",
                details={"tool": self.name, "deleted": True},
            )
            response = _DeleteTransactionResponse(deleted=True)
            return ToolSuccess(data=response)
        except ApplicationError as e:
            self.logger.warning(
                "Tool rejected operation",
                details={"tool": self.name, "error_code": e.code},
            )
            return ToolFailure.application_error(e)
        except Exception as e:
            self.logger.exception(
                "Tool failed",
                exception=e,
                details={"tool": self.name},
            )
            return ToolFailure.unexpected_error()
