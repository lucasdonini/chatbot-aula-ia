from langgraph.graph import StateGraph, START, END
from langgraph.checkpoint.memory import MemorySaver

from src.model.common.graph_state import GraphState
from .agenda import agenda_app
from .faq_reader import faq_reader_app
from .router import router_node
from .financial import financial_app
from .orquestrator import orquestrator_node
from .guardrails import input_guardrail_node, output_guardrail_node

import logging

logger = logging.getLogger(__file__)


def chose_specialist(state: GraphState) -> str:
    """Lê o protocolo do roteador e devolve o nome do próximo nó."""
    text = state["input"].strip()

    if not text.startswith("ROUTE="):
        return "fim"  # resposta direta já foi escrita no nó do roteador

    route = text.split("\n", 1)[0].split("=", 1)[1].strip()
    return route if route else "fim"


graph = StateGraph(GraphState)

graph.add_node("roteador", router_node)
graph.add_node("financeiro", financial_app)
graph.add_node("agenda", agenda_app)
graph.add_node("faq", faq_reader_app)
graph.add_node("orquestrador", orquestrator_node)
graph.add_node("guardrail_entrada", input_guardrail_node)
graph.add_node("guardrail_saida", output_guardrail_node)

graph.add_edge(START, "guardrail_entrada")
graph.add_conditional_edges(
    "guardrail_entrada",
    lambda x: x["route"] if x["route"] == "roteador" else "fim",
    {"roteador": "roteador", "fim": END},
)
graph.add_conditional_edges(
    "roteador",
    chose_specialist,
    {"financeiro": "financeiro", "agenda": "agenda", "faq": "faq", "fim": END},
)
graph.add_edge("financeiro", "orquestrador")
graph.add_edge("agenda", "orquestrador")
graph.add_edge("orquestrador", "guardrail_saida")
graph.add_edge("guardrail_saida", END)
graph.add_edge("faq", END)

# Memória centralizada no grafo — persiste o Estado inteiro entre turns
memory = MemorySaver()
agent_flux = graph.compile(checkpointer=memory)


def execute_agent_flux(user_input: str, session_id: str) -> str:
    initial_state: GraphState = {
        "messages": [{"role": "human", "content": user_input}],
        "called_agents": [],
        "route": "",
        "pii_map": {},
    }

    final_state: GraphState = agent_flux.invoke(
        initial_state, config={"configurable": {"thread_id": session_id}}
    )

    logger.debug("Called agents: %s", final_state["called_agents"])
    return final_state["messages"][-1].text
