from typing import Annotated, cast

from fastapi import Depends, Request
from langchain_groq import ChatGroq

from .application.ports.agent_graph import AgentGraph
from .services.chat_session_service import ChatSessionService
from .services.session_summary_service import SessionSummaryService


def get_session_id(request: Request) -> str:
    return cast(str, request.app.state.session_id)


def get_graph(request: Request) -> AgentGraph:
    graph = request.app.state.graph
    assert isinstance(graph, AgentGraph)
    return graph


def get_session_summary_service(request: Request) -> SessionSummaryService:
    fast_llm = request.app.state.fast_llm
    assert isinstance(fast_llm, ChatGroq)
    return SessionSummaryService(fast_llm)


def get_chat_session_service(
    session_summary_service: Annotated[
        SessionSummaryService,
        Depends(get_session_summary_service),
    ],
) -> ChatSessionService:
    return ChatSessionService(session_summary_service)
