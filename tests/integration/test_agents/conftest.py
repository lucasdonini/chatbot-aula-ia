from collections.abc import Generator
from contextlib import nullcontext
from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.application.ports.logger import Logger
from app.infrastructure.agents import build_agent_graph
from app.infrastructure.agents._core.factories.langchain_agent_factory import (
    LangChainAgentFactory,
)
from app.infrastructure.agents.financial import FinancialAgentNode
from app.infrastructure.agents.financial.tools import (
    AddTransactionTool,
    DailyBalanceTool,
    DeleteTransactionTool,
    RestoreTransactionTool,
    SearchTransactionsTool,
    TotalBalanceTool,
    UpdateTransactionTool,
)
from app.infrastructure.clock import FixedClock
from app.infrastructure.llms import fast_llm, llm_gemini
from app.infrastructure.text_generator import LLMTextGenerator
from app.services.chat_history_service import ChatHistoryService


@pytest.fixture
def application_clock() -> FixedClock:
    return FixedClock(
        datetime(2026, 8, 12, 15, 0, tzinfo=timezone.utc),
        "America/Sao_Paulo",
    )


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


@pytest.fixture
def financial_agent_node(transaction_service, application_clock) -> FinancialAgentNode:
    logger = MagicMock(spec=Logger)
    tools = (
        TotalBalanceTool(service=transaction_service, logger=logger),
        DailyBalanceTool(service=transaction_service, logger=logger),
        SearchTransactionsTool(service=transaction_service, logger=logger),
        AddTransactionTool(service=transaction_service, logger=logger),
        UpdateTransactionTool(service=transaction_service, logger=logger),
        DeleteTransactionTool(service=transaction_service, logger=logger),
        RestoreTransactionTool(service=transaction_service, logger=logger),
    )
    return FinancialAgentNode(
        LangChainAgentFactory(llm=llm_gemini, tools=tools),
        logger=logger,
        clock=application_clock,
    )


@pytest.fixture
def agent_graph(transaction_service, application_clock):
    return build_agent_graph(
        transaction_service=transaction_service,
        chat_history_service=ChatHistoryService(logger=MagicMock()),
        text_generator=LLMTextGenerator(fast_llm),
        logger_factory=lambda _: MagicMock(spec=Logger),
        trace_context_factory=lambda _: nullcontext(),
        interaction_incrementer=lambda: 1,
        clock=application_clock,
    )


@pytest.fixture(autouse=True)
def clear_active_sessions() -> Generator:
    from app.services import chat_session_service

    chat_session_service._active_sessions.clear()
    yield
    chat_session_service._active_sessions.clear()
