import logging
import uuid
from typing import cast

from langchain_core.messages import (
    AIMessage as LangGraphAIMessage,
)
from langchain_core.messages import (
    HumanMessage as LangGraphHumanMessage,
)
from langgraph.checkpoint.memory import MemorySaver
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
from langgraph.graph import END, START, StateGraph
from langgraph.graph.state import CompiledStateGraph

from app.domain.model.chat_entry import AssistantMessage, HumanMessage
from app.infrastructure.logger import increment_interaction, set_trace_context

from .agenda import AGENDA_NODE_NAME, agenda_node
from .faq import FAQ_NODE_NAME, faq_node
from .financial import FINANCIAL_NODE_NAME, financial_node
from .guardrails import (
    INPUT_GUARDRAIL_NODE_NAME,
    OUTPUT_GUARDRAIL_NODE_NAME,
    input_guardrail_node,
    output_guardrail_node,
)
from .orquestrator import ORQUESTRATOR_NODE_NAME, orquestrator_node
from .router import ROUTER_NODE_NAME, router_node
from .schema.graph_state import GraphState

logger = logging.getLogger(__name__)


class AgentGraphImpl:
    def __init__(self) -> None:
        self._SPECIALIST_NODES = {
            FAQ_NODE_NAME,
            FINANCIAL_NODE_NAME,
            AGENDA_NODE_NAME,
        }

    def _build_graph(self) -> CompiledStateGraph:
        def _chose_specialist(state: GraphState) -> str:
            """Lê o protocolo do roteador e devolve o nome do próximo nó."""
            text = state["messages"][-1].text.strip()

            if not text.startswith("ROUTE="):
                return END  # resposta direta já foi escrita no nó do roteador

            route = text.split("\n", 1)[0].split("=", 1)[1].strip()
            return route if route and route in self._SPECIALIST_NODES else END

        def _redirect_from_input_guardrail(state: GraphState) -> str:
            route = state["route"]
            return route if route and route == ROUTER_NODE_NAME else END

        graph = StateGraph(GraphState)

        graph.add_node(ROUTER_NODE_NAME, router_node)
        graph.add_node(FINANCIAL_NODE_NAME, financial_node)
        graph.add_node(AGENDA_NODE_NAME, agenda_node)
        graph.add_node(FAQ_NODE_NAME, faq_node)
        graph.add_node(ORQUESTRATOR_NODE_NAME, orquestrator_node)
        graph.add_node(INPUT_GUARDRAIL_NODE_NAME, input_guardrail_node)
        graph.add_node(OUTPUT_GUARDRAIL_NODE_NAME, output_guardrail_node)

        graph.add_edge(START, INPUT_GUARDRAIL_NODE_NAME)
        graph.add_conditional_edges(
            INPUT_GUARDRAIL_NODE_NAME, _redirect_from_input_guardrail
        )
        graph.add_conditional_edges(ROUTER_NODE_NAME, _chose_specialist)
        graph.add_edge(FINANCIAL_NODE_NAME, ORQUESTRATOR_NODE_NAME)
        graph.add_edge(AGENDA_NODE_NAME, ORQUESTRATOR_NODE_NAME)
        graph.add_edge(ORQUESTRATOR_NODE_NAME, OUTPUT_GUARDRAIL_NODE_NAME)
        graph.add_edge(OUTPUT_GUARDRAIL_NODE_NAME, END)
        graph.add_edge(FAQ_NODE_NAME, END)

        # Memória centralizada no grafo — persiste o Estado inteiro entre turns
        json_serializer = JsonPlusSerializer(
            allowed_msgpack_modules=[("app.model.graph_state", "GraphStateKeys")]
        )
        memory = MemorySaver(serde=json_serializer)
        return graph.compile(checkpointer=memory)

    def initialize(self) -> None:
        self._agent_flux = self._build_graph()

    async def execute_agent_flux(
        self, user_input: HumanMessage, session_id: str
    ) -> AssistantMessage:
        increment_interaction()
        trace_id = str(uuid.uuid4())
        set_trace_context(trace_id)
        message = LangGraphHumanMessage(id=trace_id, content=user_input.content)
        logger.info(
            "User input received",
            extra={"details": {"input": user_input.content}},
        )

        initial_state: GraphState = {
            "messages": [message],
            "called_agents": [],
            "route": "",
            "pii_map": {},
        }

        final_state_raw = await self._agent_flux.ainvoke(
            initial_state, config={"configurable": {"thread_id": session_id}}
        )
        final_state = cast(GraphState, final_state_raw)

        logger.info(
            "Agent chain completed",
            extra={"details": {"chain": " → ".join(final_state["called_agents"])}},
        )

        last = final_state["messages"][-1]
        if not isinstance(last, LangGraphAIMessage):
            raise ValueError(
                "Expected last message to be AIMessage, "
                f"received {type(last).__name__!r}"
            )
        if not isinstance(last.content, str):
            raise ValueError(
                "Excepted last message's content to be str, "
                f"received {type(last.content).__name__!r}"
            )
        return AssistantMessage(content=last.content)
