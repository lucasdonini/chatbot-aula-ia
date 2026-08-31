from contextlib import nullcontext
from typing import Any, ClassVar
from unittest.mock import MagicMock

import pytest
from langchain_core.messages import AIMessage
from langchain_core.messages import HumanMessage as GraphHumanMessage
from langgraph.graph import END

from app.application.ports.logger import Logger
from app.domain.model.chat_entry import AssistantMessage, HumanMessage
from app.infrastructure.agents._core.contracts.agent_node import AgentNode
from app.infrastructure.agents._core.specialist import SpecialistRegistration
from app.infrastructure.agents._core.state import GraphState, GraphStateKeys
from app.infrastructure.agents.graph import AgentGraphImpl


class _InputGuardrail(AgentNode):
    name: ClassVar[str] = "input_guardrail"

    async def __call__(self, state: GraphState) -> dict[GraphStateKeys, Any]:
        blocked = state["messages"][-1].content == "blocked"
        result: dict[GraphStateKeys, Any] = {
            GraphStateKeys.CALLED_AGENTS: [self.name],
            GraphStateKeys.ROUTE: END if blocked else "router",
        }
        if blocked:
            result[GraphStateKeys.MESSAGES] = [AIMessage(content="Bloqueado")]
        return result


class _Router(AgentNode):
    name: ClassVar[str] = "router"

    async def __call__(self, state: GraphState) -> dict[GraphStateKeys, Any]:
        question = state["messages"][-1].content
        return {
            GraphStateKeys.CALLED_AGENTS: [self.name],
            GraphStateKeys.MESSAGES: [AIMessage(content=f"ROUTE={question}")],
        }


class _Financial(AgentNode):
    name: ClassVar[str] = "financial"

    async def __call__(self, state: GraphState) -> dict[GraphStateKeys, Any]:
        return {
            GraphStateKeys.CALLED_AGENTS: [self.name],
            GraphStateKeys.MESSAGES: [AIMessage(content=self.name)],
        }


class _Agenda(_Financial):
    name: ClassVar[str] = "agenda"


class _Orquestrator(_Financial):
    name: ClassVar[str] = "orquestrator"


class _OutputGuardrail(_Financial):
    name: ClassVar[str] = "output_guardrail"


@pytest.fixture
def graph() -> AgentGraphImpl:
    return AgentGraphImpl(
        input_guardrail=_InputGuardrail(),
        router=_Router(),
        specialists=[
            SpecialistRegistration(node, node.name, "orquestrator")
            for node in (_Financial(), _Agenda())
        ],
        orquestrator=_Orquestrator(),
        output_guardrail=_OutputGuardrail(),
        execution_timeout_seconds=5,
        logger_factory=lambda _: MagicMock(spec=Logger),
        trace_context_factory=lambda _: nullcontext(),
        interaction_incrementer=lambda: 1,
    )


@pytest.mark.asyncio
async def test_each_turn_resets_agents_but_preserves_messages(
    graph: AgentGraphImpl,
) -> None:
    first = await graph.execute_agent_flux(HumanMessage(content="financial"), "session")
    second = await graph.execute_agent_flux(HumanMessage(content="agenda"), "session")

    assert first.message == AssistantMessage(content="output_guardrail")
    assert first.called_agents == (
        "input_guardrail",
        "router",
        "financial",
        "orquestrator",
        "output_guardrail",
    )
    assert second.called_agents == (
        "input_guardrail",
        "router",
        "agenda",
        "orquestrator",
        "output_guardrail",
    )
    snapshot = await graph._agent_flux.aget_state(
        {"configurable": {"thread_id": "session"}}
    )
    assert snapshot.values["called_agents"] == list(second.called_agents)
    assert [
        message.content
        for message in snapshot.values["messages"]
        if isinstance(message, GraphHumanMessage)
    ] == ["financial", "agenda"]
    graph._logger.info.assert_called_with(
        "Agent chain completed",
        details={"chain": " → ".join(second.called_agents)},
    )


@pytest.mark.asyncio
async def test_blocked_turn_only_reports_input_guardrail_and_next_turn_recovers(
    graph: AgentGraphImpl,
) -> None:
    await graph.execute_agent_flux(HumanMessage(content="financial"), "session")
    blocked = await graph.execute_agent_flux(HumanMessage(content="blocked"), "session")

    assert blocked.message.content == "Bloqueado"
    assert blocked.called_agents == ("input_guardrail",)

    following = await graph.execute_agent_flux(
        HumanMessage(content="agenda"), "session"
    )
    assert following.called_agents == (
        "input_guardrail",
        "router",
        "agenda",
        "orquestrator",
        "output_guardrail",
    )


@pytest.mark.asyncio
async def test_router_early_exit_does_not_inherit_previous_specialists(
    graph: AgentGraphImpl,
) -> None:
    await graph.execute_agent_flux(HumanMessage(content="financial"), "session")
    result = await graph.execute_agent_flux(HumanMessage(content="unknown"), "session")

    assert result.called_agents == ("input_guardrail", "router")
