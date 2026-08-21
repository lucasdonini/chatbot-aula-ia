from unittest.mock import AsyncMock, MagicMock

from app.infrastructure.agents import AgentGraphImpl, build_agent_graph
from app.services.transaction_service import TransactionService


def test_build_agent_graph_returns_initialized_graph() -> None:
    transaction_service = TransactionService.__new__(TransactionService)
    object.__setattr__(transaction_service, "_repository", None)
    text_generator = MagicMock()
    text_generator.generate = AsyncMock(return_value="CATEGORIA: APROVADO")

    graph = build_agent_graph(
        transaction_service=transaction_service,
        text_generator=text_generator,
    )

    assert isinstance(graph, AgentGraphImpl)
    assert not hasattr(graph, "initialize")
