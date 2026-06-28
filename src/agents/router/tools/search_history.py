import logging
from typing import List

from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from src.infrastructure.execution_time_logger import log_execution_time
from src.model.chat_session import ChatSession
from src.services.chat_history_service import ChatHistoryService

logger = logging.getLogger(__name__)


class SearchHistoryArgsSchema(BaseModel):
    search: str = Field(
        ..., description="A expressão procurada no histórico através de regex"
    )


class SearchHistoryTool(BaseTool):
    args_schema: type[BaseModel] = SearchHistoryArgsSchema
    name: str = "search_history"
    description: str = (
        "Consulta conversas ANTERIORES do usuário (sessões já encerradas).\n\n"
        "Use SOMENTE quando a resposta depende de algo dito numa conversa passada"
        "— preferências, decisões ou planos que o usuário mencionou antes."
        "NÃO use para dados que estão no banco (gastos, saldos, eventos): isso é "
        "responsabilidade dos agentes especialistas que têm acesso a tools mais "
        "específicas para isso."
    )

    service: ChatHistoryService = Field(exclude=True)

    def _format_history(self, history: List[ChatSession]) -> str:
        return "\n\n".join(f"[{h.started_at:%d/%m/%Y}] {h.summary}" for h in history)

    def _run(self, *args, **kwargs) -> str:
        raise NotImplementedError("This tool is stricktly assyncronal. Use _arun.")

    @log_execution_time
    async def _arun(self, search: str) -> str:
        logger.info("%s tool called (search: %s)", self.name, search)
        try:
            history = await self.service.fetch_history(search=search, limit=3)
            return (
                self._format_history(history)
                if history
                else "Nenhuma conversa anterior relevante foi encontrada."
            )

        except Exception as e:
            logger.exception("Failed to search history", e)
            return f"Erro ao buscar as mensagens: {str(e)}"
