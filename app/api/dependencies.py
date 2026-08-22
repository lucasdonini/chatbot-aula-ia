from typing import cast

from fastapi import Request

from ..application.ports.agent_graph import AgentGraph
from ..services.chat_session_service import ChatSessionService
from ..services.session_summary_service import SessionSummaryService


def get_session_id(request: Request) -> str:
    return cast(str, request.app.state.session_id)


def get_graph(request: Request) -> AgentGraph:
    graph = request.app.state.graph
    assert isinstance(graph, AgentGraph)
    return graph


def get_session_summary_service(request: Request) -> SessionSummaryService:
    service = request.app.state.session_summary_service
    assert isinstance(service, SessionSummaryService)
    return service


def get_chat_session_service(
    request: Request,
) -> ChatSessionService:
    service = request.app.state.chat_session_service
    assert isinstance(service, ChatSessionService)
    return service
