from typing import Any

from langgraph.graph import END

from app.infrastructure.agents._core.contracts.agent_node import AgentNode
from app.infrastructure.agents._core.specialist import SpecialistRegistration
from app.infrastructure.agents._core.state import GraphState, GraphStateKeys
from app.infrastructure.agents.router.router_prompt import build_router_prompt


class _FinancialNode(AgentNode):
    name = "financial"

    async def __call__(self, state: GraphState) -> dict[GraphStateKeys, Any]:
        return {}


class _AgendaNode(AgentNode):
    name = "agenda"

    async def __call__(self, state: GraphState) -> dict[GraphStateKeys, Any]:
        return {}


def test_build_router_prompt_uses_registered_specialists() -> None:
    specialists = (
        SpecialistRegistration(
            node=_FinancialNode(),
            description="finanças pessoais",
            destination=END,
        ),
        SpecialistRegistration(
            node=_AgendaNode(),
            description="compromissos e horários",
            destination=END,
        ),
    )

    prompt = build_router_prompt(
        specialists=specialists,
        search_history_tool_name="custom_memory_lookup",
    )

    assert "financial: finanças pessoais" in prompt
    assert "agenda: compromissos e horários" in prompt
    assert "financial | agenda" in prompt
    assert "custom_memory_lookup" in prompt
    assert "search_history" not in prompt


def test_build_router_prompt_rejects_empty_catalog() -> None:
    try:
        build_router_prompt(specialists=(), search_history_tool_name="search_history")
    except ValueError as exc:
        assert str(exc) == "Router requires at least one specialist"
    else:
        raise AssertionError("Expected empty specialist catalog to be rejected")
