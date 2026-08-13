import logging
from typing import Any, Dict

from langchain.agents import create_agent
from langchain_core.messages import SystemMessage

from app.agents.llms import specialist_llm
from app.agents.temporal_context import build_temporal_context
from app.infrastructure.execution_time_logger import log_execution_time
from app.model.graph_state import GraphState, GraphStateKeys
from app.model.specialist_output import AgendaOutput

from .agenda_prompt import AGENDA_NODE_NAME, PROMPT

logger = logging.getLogger(__name__)

agenda_agent = create_agent(
    model=specialist_llm,  # type: ignore[arg-type]
    system_prompt=PROMPT,
    response_format=AgendaOutput,
)


@log_execution_time
async def agenda_node(state: GraphState) -> Dict[GraphStateKeys, Any]:
    input_text = state["messages"][-1].content[:500]
    logger.info(
        "Agent called",
        extra={"details": {"name": AGENDA_NODE_NAME, "input": input_text}},
    )
    request_state: GraphState = {
        **state,
        "messages": [
            SystemMessage(content=build_temporal_context()),
            *state["messages"],
        ],
    }
    response = await agenda_agent.ainvoke(request_state)  # type: ignore[arg-type]
    last = (response.get("messages") or [None])[-1]
    output = last.content[:500] if last and last.content else "(tool call)"
    logger.info(
        "Agent response",
        extra={"details": {"from": AGENDA_NODE_NAME, "output": output}},
    )
    return {
        GraphStateKeys.MESSAGES: response.get("messages") or [],
        GraphStateKeys.CALLED_AGENTS: [AGENDA_NODE_NAME],
    }
