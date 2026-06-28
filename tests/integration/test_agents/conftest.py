from collections.abc import Generator
from unittest.mock import AsyncMock, patch

import pytest


def _make_aimessage(content: str = "", tool_calls: list | None = None):
    from langchain_core.messages import AIMessage

    return AIMessage(content=content, tool_calls=tool_calls or [])


def tool_call_dict(name: str, args: dict, call_id: str | None = None) -> dict:
    return {
        "name": name,
        "args": args,
        "id": call_id or f"call_{name}",
    }


@pytest.fixture
def mock_gemini_ainvoke() -> Generator[AsyncMock, None, None]:
    with patch(
        "langchain_google_genai.chat_models.ChatGoogleGenerativeAI.ainvoke",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


@pytest.fixture
def mock_groq_ainvoke() -> Generator[AsyncMock, None, None]:
    with patch(
        "langchain_groq.chat_models.ChatGroq.ainvoke",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


@pytest.fixture
def mock_all_llms(
    mock_gemini_ainvoke: AsyncMock,
    mock_groq_ainvoke: AsyncMock,
) -> dict[str, AsyncMock]:
    return {
        "gemini": mock_gemini_ainvoke,
        "groq": mock_groq_ainvoke,
    }


@pytest.fixture(autouse=True)
def clear_active_sessions() -> Generator:
    from src.services import chat_session_service

    chat_session_service._active_sessions.clear()
    yield
    chat_session_service._active_sessions.clear()
