import asyncio
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.domain.model.chat_entry import HumanMessage
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


@pytest.mark.asyncio
async def test_agent_graph_times_out() -> None:
    transaction_service = TransactionService.__new__(TransactionService)
    object.__setattr__(transaction_service, "_repository", None)
    text_generator = MagicMock()
    text_generator.generate = AsyncMock(return_value="CATEGORIA: APROVADO")
    graph = build_agent_graph(
        transaction_service=transaction_service,
        text_generator=text_generator,
        execution_timeout_seconds=0.01,
    )

    async def wait_forever(*args: object, **kwargs: object) -> None:
        await asyncio.Event().wait()

    graph._agent_flux.ainvoke = AsyncMock(side_effect=wait_forever)

    with pytest.raises(TimeoutError):
        await graph.execute_agent_flux(
            HumanMessage(content="teste"),
            session_id="timeout-test",
        )
