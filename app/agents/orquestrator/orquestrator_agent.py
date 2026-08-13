import logging
from typing import Any, Dict

from langchain.agents import create_agent
from langchain_core.messages import SystemMessage

from app.agents.llms import fast_llm
from app.agents.temporal_context import build_temporal_context
from app.infrastructure.execution_time_logger import log_execution_time
from app.model.graph_state import GraphState, GraphStateKeys

from .orquestrator_prompt import PROMPT

logger = logging.getLogger(__name__)

ORQUESTRATOR_NODE_NAME = "orquestrator"
orquestrator_agent = create_agent(
    model=fast_llm,  # type: ignore[arg-type]
    system_prompt=PROMPT,
)


@log_execution_time
async def orquestrator_node(state: GraphState) -> Dict[GraphStateKeys, Any]:
    input_text = state["messages"][-1].content[:500]
    logger.info(
        "Agent called",
        extra={"details": {"name": ORQUESTRATOR_NODE_NAME, "input": input_text}},
    )
    request_state: GraphState = {
        **state,
        "messages": [
            SystemMessage(content=build_temporal_context()),
            *state["messages"],
        ],
    }
    response = await orquestrator_agent.ainvoke(request_state)  # type: ignore[arg-type]
    last = (response.get("messages") or [None])[-1]
    output = last.content[:500] if last and last.content else "(tool call)"
    logger.info(
        "Agent response",
        extra={"details": {"from": ORQUESTRATOR_NODE_NAME, "output": output}},
    )
    return {
        GraphStateKeys.MESSAGES: response.get("messages") or [],
        GraphStateKeys.CALLED_AGENTS: [ORQUESTRATOR_NODE_NAME],
    }
