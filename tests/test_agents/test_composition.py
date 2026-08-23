import asyncio
from contextlib import nullcontext
from datetime import datetime, timezone
from typing import Any, ClassVar
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.application.ports.logger import Logger
from app.domain.model.chat_entry import HumanMessage
from app.infrastructure.agents import AgentGraphImpl, build_agent_graph
from app.infrastructure.agents._core.contracts.agent_node import AgentNode
from app.infrastructure.agents._core.state import GraphState, GraphStateKeys
from app.infrastructure.clock import FixedClock
from app.services.chat_history_service import ChatHistoryService
from app.services.transaction_service import TransactionService


class _StubNode(AgentNode):
    name: ClassVar[str] = "stub"

    async def __call__(self, state: GraphState) -> dict[GraphStateKeys, Any]:
        return {}


def _fixed_clock() -> FixedClock:
    return FixedClock(
        datetime(2026, 8, 12, 15, 0, tzinfo=timezone.utc),
        "America/Sao_Paulo",
    )


def test_build_agent_graph_returns_initialized_graph() -> None:
    transaction_service = TransactionService.__new__(TransactionService)
    object.__setattr__(transaction_service, "_repository", None)
    text_generator = MagicMock()
    text_generator.generate = AsyncMock(return_value="CATEGORIA: APROVADO")

    graph = build_agent_graph(
        transaction_service=transaction_service,
        chat_history_service=MagicMock(spec=ChatHistoryService),
        text_generator=text_generator,
        logger_factory=lambda _: MagicMock(spec=Logger),
        trace_context_factory=lambda _: nullcontext(),
        interaction_incrementer=lambda: 1,
        clock=_fixed_clock(),
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
        chat_history_service=MagicMock(spec=ChatHistoryService),
        text_generator=text_generator,
        logger_factory=lambda _: MagicMock(spec=Logger),
        trace_context_factory=lambda _: nullcontext(),
        interaction_incrementer=lambda: 1,
        clock=_fixed_clock(),
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


@pytest.mark.asyncio
async def test_graph_times_node_with_injected_logger() -> None:
    logger = MagicMock(spec=Logger)
    graph = AgentGraphImpl.__new__(AgentGraphImpl)
    graph._logger = logger
    timed_node = graph._timed_node(_StubNode())

    result = await timed_node.ainvoke(
        {"messages": [], "called_agents": [], "route": "", "pii_map": {}}
    )

    assert result == {}
    logger.debug.assert_called_once()
    assert logger.debug.call_args.args == ("Function finished",)
    assert logger.debug.call_args.kwargs["details"]["function"] == "stub"


def test_build_agent_graph_shares_application_clock_with_temporal_nodes() -> None:
    transaction_service = TransactionService.__new__(TransactionService)
    object.__setattr__(transaction_service, "_repository", None)
    text_generator = MagicMock()
    text_generator.generate = AsyncMock(return_value="CATEGORIA: APROVADO")
    clock = _fixed_clock()

    graph = build_agent_graph(
        transaction_service=transaction_service,
        chat_history_service=MagicMock(spec=ChatHistoryService),
        text_generator=text_generator,
        logger_factory=lambda _: MagicMock(spec=Logger),
        trace_context_factory=lambda _: nullcontext(),
        interaction_incrementer=lambda: 1,
        clock=clock,
    )

    temporal_nodes = (
        graph._router,
        graph._orquestrator,
        *(specialist.node for specialist in graph._specialists[:-1]),
    )
    assert all(node._clock is clock for node in temporal_nodes)
