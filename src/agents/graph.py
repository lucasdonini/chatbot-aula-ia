import logging

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import HumanMessage, AIMessage
from langgraph.checkpoint.memory import MemorySaver

from src.model.common.graph_state import GraphState
from .agenda import agenda_agent, AGENDA_NODE_NAME
from .faq import faq_agent, FAQ_NODE_NAME
from .router import router_agent, ROUTER_NODE_NAME
from .financial import financial_agent, FINANCIAL_NODE_NAME
from .orquestrator import orquestrator_agent, ORQUESTRATOR_NODE_NAME
from .guardrails import (
    input_guardrail_node,
    output_guardrail_node,
    INPUT_GUARDRAIL_NODE_NAME,
    OUTPUT_GUARDRAIL_NODE_NAME,
)

logger = logging.getLogger(__file__)

SPECIALIST_NODES = {
    FAQ_NODE_NAME,
    FINANCIAL_NODE_NAME,
    AGENDA_NODE_NAME,
}


def _chose_specialist(state: GraphState) -> str:
    """Lê o protocolo do roteador e devolve o nome do próximo nó."""
    text = state["messages"][-1].text.strip()

    if not text.startswith("ROUTE="):
        return END  # resposta direta já foi escrita no nó do roteador

    route = text.split("\n", 1)[0].split("=", 1)[1].strip()
    return route if route and route in SPECIALIST_NODES else END


def _redirect_from_input_guardrail(state: GraphState) -> str:
    route = state["route"]
    return route if route and route == ROUTER_NODE_NAME else END


graph = StateGraph(GraphState)

graph.add_node(ROUTER_NODE_NAME, router_agent)
graph.add_node(FINANCIAL_NODE_NAME, financial_agent)
graph.add_node(AGENDA_NODE_NAME, agenda_agent)
graph.add_node(FAQ_NODE_NAME, faq_agent)
graph.add_node(ORQUESTRATOR_NODE_NAME, orquestrator_agent)
graph.add_node(INPUT_GUARDRAIL_NODE_NAME, input_guardrail_node)
graph.add_node(OUTPUT_GUARDRAIL_NODE_NAME, output_guardrail_node)

graph.add_edge(START, INPUT_GUARDRAIL_NODE_NAME)
graph.add_conditional_edges(INPUT_GUARDRAIL_NODE_NAME, _redirect_from_input_guardrail)
graph.add_conditional_edges(ROUTER_NODE_NAME, _chose_specialist)
graph.add_edge(FINANCIAL_NODE_NAME, ORQUESTRATOR_NODE_NAME)
graph.add_edge(AGENDA_NODE_NAME, ORQUESTRATOR_NODE_NAME)
graph.add_edge(ORQUESTRATOR_NODE_NAME, OUTPUT_GUARDRAIL_NODE_NAME)
graph.add_edge(OUTPUT_GUARDRAIL_NODE_NAME, END)
graph.add_edge(FAQ_NODE_NAME, END)

# Memória centralizada no grafo — persiste o Estado inteiro entre turns
memory = MemorySaver()
agent_flux = graph.compile(checkpointer=memory)


def execute_agent_flux(user_input: str, session_id: str) -> str:
    initial_state: GraphState = {
        "messages": [HumanMessage(content=user_input)],
        "called_agents": [],
        "route": "",
        "pii_map": {},
    }

    final_state: GraphState = agent_flux.invoke(
        initial_state, config={"configurable": {"thread_id": session_id}}
    )

    logger.debug("Called agents: %s", final_state["called_agents"])
    return final_state["messages"][-1].text
