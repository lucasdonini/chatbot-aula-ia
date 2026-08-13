import logging
import traceback
from typing import List

from langchain_groq import ChatGroq

from app.infrastructure.execution_time_logger import log_execution_time
from app.infrastructure.settings import settings
from app.model.chat_session import ChatEntry, ChatMessage

logger = logging.getLogger(__name__)

_MESSAGES_SUMMARY_PROMPT = """\
Você é um assistente que resume conversas de assessoria financeira e agenda.
Gere um resumo conciso em 2-4 frases capturando:
- O que o usuário fez (transações registradas, eventos agendados)
- O que o usuário perguntou
- Informações relevantes mencionadas (valores, datas, categorias)

Responda APENAS com o resumo, sem introdução ou explicação.

Conversa:
{conversa}
"""

_EXCEPTION_SUMMARY_PROMPT = """\
Você é responsável por converter exceções internas da 
aplicação em uma explicação curta e amigável para o usuário.

Sua resposta será armazenada no histórico de uma conversa e poderá ser utilizada 
posteriormente por outro agente para responder perguntas sobre o que aconteceu.

Objetivo:
Gerar um resumo fiel do erro em linguagem natural.

Regras:
- Escreva no máximo duas frases.
- Explique apenas o que aconteceu, não como corrigir.
- Não invente informações que não estejam evidentes no erro.
- Não mencione nomes de classes, funções, arquivos, 
    linhas de código ou stack traces.
- Não exponha detalhes internos da aplicação.
- Se a causa do erro estiver clara, mencione-a de forma simples.
- Se a causa não puder ser determinada com segurança, 
    diga apenas que ocorreu um erro interno inesperado.
- Escreva como se estivesse registrando um fato ocorrido 
    durante a conversa, e não respondendo diretamente ao usuário.
- Não use primeira pessoa ("eu", "nós").

Stack trace:
<stack_trace>
{}
</stack_trace>

Retorne apenas o resumo.
"""


class SessionSummaryService:
    def __init__(self) -> None:
        self._llm = ChatGroq(
            model="llama-3.3-70b-versatile",
            temperature=0.0,
            api_key=settings.groq_api_key,
        )

    def _format_conversation(self, entries: List[ChatEntry]) -> str:
        """Formats entries array for summary"""
        lines = []
        for entry in entries:
            if isinstance(entry, ChatMessage):
                lines.append(f"{entry.role.value}: {entry.content}")
            else:
                lines.append(f"ERROR: {entry.exception} -> {entry.summary}")
        return "\n".join(lines)

    @log_execution_time
    async def summarize_session(self, entries: List[ChatEntry]) -> str:
        """Summarizes the session's entries"""
        logger.debug(
            "Summarizing entries",
            extra={"details": {"entry_count": len(entries)}},
        )

        conversation = self._format_conversation(entries)
        response = (
            await self._llm.ainvoke(
                _MESSAGES_SUMMARY_PROMPT.format(conversa=conversation)
            )
        ).content

        if not isinstance(response, str):
            raise TypeError(
                f"Summarizer returned non-text content: {type(response).__name__!r}"
            )

        return response.strip()

    async def summarize_exception(self, exc: Exception) -> str:
        """Summarizes the erro's traceback into a couple of friendly lines."""
        logger.debug(
            "Summarizing error", extra={"details": {"exec_name": type(exc).__name__}}
        )

        stack_trace = traceback.format_exception(type(exc), exc, exc.__traceback__)
        response = (
            await self._llm.ainvoke(_EXCEPTION_SUMMARY_PROMPT.format(stack_trace))
        ).content

        if not isinstance(response, str):
            raise TypeError(
                f"Summarizer returned non-text content: {type(response).__name__!r}"
            )

        return response.strip()
