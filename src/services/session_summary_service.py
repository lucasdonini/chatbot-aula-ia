import logging
import time
from typing import List

from langchain_groq import ChatGroq

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
    def __init__(self):
        self._llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.0,
            api_key=settings.groq_api_key,
        )

    def sumarize(self, messages: List[ChatMessage]) -> str:
        """Calls llm for summary"""
        logger.info("Sumarizing messages...")
        start_time = time.perf_counter()

        conversation = self._format_conversation(messages)
        response = self._llm.invoke(_SUMMARY_PROMPT.format(conversa=conversation))

        end_time = time.perf_counter()
        logger.info("Messages sumarized. Time: %s", end_time - start_time)
        return response.content.strip()

    def _format_conversation(messages: List[ChatMessage]) -> str:
        """Formats message array for summary"""
        lines = [f"{msg.role}: {msg.content}" for msg in messages]
        return "\n".join(lines)
