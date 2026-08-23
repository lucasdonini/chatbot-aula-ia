from typing import Any

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.application.ports.logger import Logger
from app.domain.model.chat_session import ChatSessionSummarized
from app.services.chat_history_service import ChatHistoryService

TOOL_NAME = "search_history"


class SearchHistoryArgsSchema(BaseModel):
    search: str = Field(
        ..., description="A expressão procurada no histórico através de regex"
    )


class SearchHistoryTool(BaseTool):
    args_schema: type[BaseModel] = SearchHistoryArgsSchema
    name: str = TOOL_NAME
    description: str = (
        "Consulta conversas ANTERIORES do usuário (sessões já encerradas).\n\n"
        "Use SOMENTE quando a resposta depende de algo dito numa conversa passada"
        "— preferências, decisões ou planos que o usuário mencionou antes."
        "NÃO use para dados que estão no banco (gastos, saldos, eventos): isso é "
        "responsabilidade dos agentes especialistas que têm acesso a tools mais "
        "específicas para isso."
    )

    service: ChatHistoryService = Field(exclude=True)
    logger: Logger = Field(exclude=True)

    def _format_history(self, history: list[ChatSessionSummarized]) -> str:
        return "\n\n".join(f"[{h.started_at:%d/%m/%Y}] {h.summary}" for h in history)

    def _run(self, *args: Any, **kwargs: Any) -> str:
        raise NotImplementedError("This tool is stricktly assyncronal. Use _arun.")

    async def _arun(self, search: str) -> str:
        self.logger.debug(
            "Tool called",
            details={"tool": self.name, "search_length": len(search)},
        )
        try:
            history = await self.service.fetch_history(search=search, limit=3)
            return (
                self._format_history(history)
                if history
                else "Nenhuma conversa anterior relevante foi encontrada."
            )

        except Exception as e:
            self.logger.exception(
                "Tool failed",
                exception=e,
                details={"tool": self.name},
            )
            return f"Erro ao buscar as mensagens: {str(e)}"
