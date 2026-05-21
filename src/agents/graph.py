from langgraph.graph import StateGraph, END
from langgraph.checkpoint.memory import MemorySaver

from src.model.common.graph_state import GraphState
from .agenda import agenda_node
from .faq_reader import faq_reader_node
from .router import router_node
from .financial import financial_node
from .orquestrator import orquestrator_node

NODE_NAMES = {
    router_node: "roteador",
    financial_node: "financeiro",
    agenda_node: "agenda",
    faq_reader_node: "faq",
    orquestrator_node: "orquestrador",
}

CONDITIONAL_EDGE_MAPPINGS = {END: "end", **NODE_NAMES}
SPECIALIST_ROUTES = tuple(
    CONDITIONAL_EDGE_MAPPINGS[node]
    for node in (financial_node, agenda_node, faq_reader_node)
)


def chose_specialist(state: GraphState) -> str:
    """Lê o protocolo do roteador e devolve o nome do próximo nó."""
    text = state["input"].strip()

    if not text.startswith("ROUTE="):
        return CONDITIONAL_EDGE_MAPPINGS[
            END
        ]  # resposta direta já foi escrita no nó do roteador

    route = text.split("\n", 1)[0].split("=", 1)[1].strip()
    return route if route in SPECIALIST_ROUTES else CONDITIONAL_EDGE_MAPPINGS[END]


graph = StateGraph(GraphState)

for node, node_name in NODE_NAMES.items():
    graph.add_node(node_name, node)

graph.set_entry_point(NODE_NAMES[router_node])

conditional_routes = {route: route for route in SPECIALIST_ROUTES}
conditional_routes[CONDITIONAL_EDGE_MAPPINGS[END]] = END
graph.add_conditional_edges(
    NODE_NAMES[router_node], chose_specialist, conditional_routes
)

graph.add_edge(NODE_NAMES[financial_node], NODE_NAMES[orquestrator_node])
graph.add_edge(NODE_NAMES[agenda_node], NODE_NAMES[orquestrator_node])
graph.add_edge(NODE_NAMES[orquestrator_node], END)
graph.add_edge(NODE_NAMES[faq_reader_node], END)  # FAQ bypassa o orquestrador

# Memória centralizada no grafo — persiste o Estado inteiro entre turns
memory = MemorySaver()
agent_flux = graph.compile(checkpointer=memory)


def execute_agent_flux(initial_state: GraphState, session_id: str) -> GraphState:
    return agent_flux.invoke(
        initial_state,
        config={"configurable": {"thread_id": session_id}},
    )
