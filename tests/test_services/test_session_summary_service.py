from unittest.mock import AsyncMock, patch

import pytest

from src.model.chat_session import ChatMessage
from src.services.session_summary_service import SessionSummaryService


class TestSessionSummaryService:
    @pytest.fixture
    def service(self):
        with patch("src.services.session_summary_service.ChatGroq") as mock_groq:
            mock_llm = AsyncMock()
            mock_groq.return_value = mock_llm
            service = SessionSummaryService()
            service._llm = mock_llm
            yield service

    @pytest.mark.asyncio
    async def test_summarize(self, service):
        messages = [
            ChatMessage(role="human", content="Gastei 100 reais"),
            ChatMessage(role="assistant", content="Registrado como despesa"),
        ]
        mock_response = AsyncMock()
        mock_response.content = "Usuário registrou despesa de 100 reais."
        service._llm.ainvoke.return_value = mock_response

        result = await service.sumarize(messages)

        assert result == "Usuário registrou despesa de 100 reais."
        service._llm.ainvoke.assert_called_once()

    def test_format_conversation(self, service):
        messages = [
            ChatMessage(role="human", content="Olá"),
            ChatMessage(role="assistant", content="Oi!"),
        ]
        result = service._format_conversation(messages)
        assert result == "human: Olá\nassistant: Oi!"

    @pytest.mark.asyncio
    async def test_summarize_empty_conversation(self, service):
        mock_response = AsyncMock()
        mock_response.content = "Nenhuma conversa para resumir."
        service._llm.ainvoke.return_value = mock_response

        result = await service.sumarize([])

        assert result == "Nenhuma conversa para resumir."

    @pytest.mark.asyncio
    async def test_summarize_calls_groq(self, service):
        messages = [ChatMessage(role="human", content="teste")]
        mock_response = AsyncMock()
        mock_response.content = "resumo"
        service._llm.ainvoke.return_value = mock_response

        await service.sumarize(messages)

        service._llm.ainvoke.assert_called_once()
        prompt_arg = service._llm.ainvoke.call_args[0][0]
        assert "{conversa}" not in prompt_arg
        assert "teste" in prompt_arg
