from typing import Any

import pytest
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


@pytest.mark.parametrize(
    ("example_title", "expected_answer"),
    [
        (
            "MEMÓRIA ENCONTRADA",
            "Roteador: Na conversa de 12/03/2026, você comentou que comprou a cadeira",
        ),
        (
            "MEMÓRIA NÃO ENCONTRADA",
            "Roteador: Não encontrei esse assunto nas conversas anteriores.",
        ),
        (
            "FALHA NA CONSULTA",
            "Roteador: Não consegui consultar o histórico agora.",
        ),
    ],
)
def test_memory_examples_use_injected_tool_and_distinct_responses(
    example_title: str, expected_answer: str
) -> None:
    prompt = build_router_prompt(
        specialists=(
            SpecialistRegistration(
                node=_FinancialNode(), description="finanças pessoais", destination=END
            ),
        ),
        search_history_tool_name="custom_memory_lookup",
    )

    example = prompt.split(f"EXEMPLO — {example_title}\n", 1)[1].split("\n\n", 1)[0]

    assert "Roteador chama custom_memory_lookup" in example
    assert expected_answer in example
    assert "ROUTE=" not in example
    assert "search_history" not in prompt
    assert prompt.index("Os exemplos abaixo são fictícios") < prompt.index(example)
    assert prompt.index(example) < prompt.index("FIM DOS EXEMPLOS")
