from collections.abc import Generator
from dataclasses import dataclass, field
from datetime import datetime, timezone
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.dependencies import get_chat_session_service, get_graph
from app.api.middleware.exception_handler import register_exception_handlers
from app.api.routes.chat import router
from app.application.ports.logger import Logger
from app.domain.model.chat_entry import AssistantMessage, ChatMessage, HumanMessage
from app.domain.model.chat_session import ChatSession
from app.infrastructure.logger import bind_session_context

_SESSION_ID = "session-123"


@dataclass
class GraphStub:
    response: AssistantMessage = field(
        default_factory=lambda: AssistantMessage(content="Resposta do assistente")
    )
    error: Exception | None = None
    messages: list[tuple[HumanMessage, str]] = field(default_factory=list)

    async def execute_agent_flux(
        self, message: HumanMessage, session_id: str
    ) -> AssistantMessage:
        self.messages.append((message, session_id))
        if self.error is not None:
            raise self.error
        return self.response


@dataclass
class SessionServiceStub:
    messages: list[tuple[str, ChatMessage]] = field(default_factory=list)
    errors: list[tuple[str, Exception]] = field(default_factory=list)
    ensured_sessions: list[str] = field(default_factory=list)

    async def get_or_create_session(self, session_id: str) -> ChatSession:
        self.ensured_sessions.append(session_id)
        return ChatSession(
            session_id=session_id,
            started_at=datetime(2026, 8, 12, tzinfo=timezone.utc),
        )

    async def save_message(self, session_id: str, message: ChatMessage) -> None:
        self.messages.append((session_id, message))

    async def save_error(self, session_id: str, error: Exception) -> None:
        self.errors.append((session_id, error))


@pytest.fixture
def graph() -> GraphStub:
    return GraphStub()


@pytest.fixture
def session_service() -> SessionServiceStub:
    return SessionServiceStub()


@pytest.fixture
def client(
    graph: GraphStub, session_service: SessionServiceStub
) -> Generator[TestClient]:
    app = FastAPI()
    app.state.session_context_factory = bind_session_context
    register_exception_handlers(
        app,
        logger=MagicMock(spec=Logger),
        session_context_factory=bind_session_context,
    )
    app.include_router(router, prefix="/api")

    def override_graph() -> GraphStub:
        return graph

    def override_session_service() -> SessionServiceStub:
        return session_service

    app.dependency_overrides[get_graph] = override_graph
    app.dependency_overrides[get_chat_session_service] = override_session_service

    with TestClient(app, raise_server_exceptions=False) as test_client:
        yield test_client


def test_chat_persists_messages_and_returns_graph_response(
    client: TestClient, graph: GraphStub, session_service: SessionServiceStub
) -> None:
    response = client.post(
        f"/api/chat/{_SESSION_ID}", json={"message": "Minha pergunta"}
    )

    assert response.status_code == 200
    assert response.json() == {
        "session_id": _SESSION_ID,
        "content": "Resposta do assistente",
    }
    assert graph.messages == [(HumanMessage(content="Minha pergunta"), _SESSION_ID)]
    assert session_service.messages == [
        (_SESSION_ID, HumanMessage(content="Minha pergunta")),
        (_SESSION_ID, AssistantMessage(content="Resposta do assistente")),
    ]
    assert session_service.errors == []
    assert session_service.ensured_sessions == [_SESSION_ID]


def test_chat_ensures_session_for_each_turn(
    client: TestClient, session_service: SessionServiceStub
) -> None:
    response = client.post(
        f"/api/chat/{_SESSION_ID}", json={"message": "Minha pergunta"}
    )

    assert response.status_code == 200
    assert session_service.ensured_sessions == [_SESSION_ID]


def test_chat_rejects_request_without_message(
    client: TestClient, graph: GraphStub, session_service: SessionServiceStub
) -> None:
    response = client.post(f"/api/chat/{_SESSION_ID}", json={})

    assert response.status_code == 422
    assert graph.messages == []
    assert session_service.messages == []


def test_chat_persists_unexpected_error_and_returns_generic_response(
    client: TestClient, graph: GraphStub, session_service: SessionServiceStub
) -> None:
    error = RuntimeError("internal detail")
    graph.error = error

    response = client.post(
        f"/api/chat/{_SESSION_ID}", json={"message": "Minha pergunta"}
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Internal Server Error"}
    assert session_service.errors == [(_SESSION_ID, error)]
    assert session_service.messages == [
        (_SESSION_ID, HumanMessage(content="Minha pergunta"))
    ]


def test_chat_timeout_is_not_persisted_as_unexpected_error(
    client: TestClient, graph: GraphStub, session_service: SessionServiceStub
) -> None:
    graph.error = TimeoutError()

    response = client.post(
        f"/api/chat/{_SESSION_ID}", json={"message": "Minha pergunta"}
    )

    assert response.status_code == 504
    assert response.json() == {
        "detail": "A operação excedeu o tempo limite. Tente novamente."
    }
    assert session_service.errors == []
    assert session_service.messages == [
        (_SESSION_ID, HumanMessage(content="Minha pergunta"))
    ]
