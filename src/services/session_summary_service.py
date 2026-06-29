import logging
from typing import List

from langchain_groq import ChatGroq

from src.infrastructure.execution_time_logger import log_execution_time
from src.infrastructure.settings import settings
from src.model.chat_session import ChatMessage

logger = logging.getLogger(__name__)

_SUMMARY_PROMPT = """\
Você é um assistente que resume conversas de assessoria financeira e agenda.
Gere um resumo conciso em 2-4 frases capturando:
- O que o usuário fez (transações registradas, eventos agendados)
- O que o usuário perguntou
- Informações relevantes mencionadas (valores, datas, categorias)

Responda APENAS com o resumo, sem introdução ou explicação.

Conversa:
{conversa}
"""


class SessionSummaryService:
    def __init__(self) -> None:
        self._llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.0,
            api_key=settings.groq_api_key,
        )

    @log_execution_time
    async def sumarize(self, messages: List[ChatMessage]) -> str:
        """Calls llm for summary"""
        logger.debug("Sumarizing messages...")

        conversation = self._format_conversation(messages)
        response = (
            await self._llm.ainvoke(_SUMMARY_PROMPT.format(conversa=conversation))
        ).content

        if not isinstance(response, str):
            raise TypeError(
                f"Summarizer returned non-text content: {type(response).__name__!r}"
            )

        return response.strip()

    def _format_conversation(self, messages: List[ChatMessage]) -> str:
        """Formats message array for summary"""
        lines = [f"{msg.role}: {msg.content}" for msg in messages]
        return "\n".join(lines)
