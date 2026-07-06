import logging
from typing import Any, Dict

from langchain.agents import create_agent

from src.infrastructure.execution_time_logger import log_execution_time
from src.model.graph_state import GraphState, GraphStateKeys

from ..llms import fast_llm
from .orquestrator_prompt import PROMPT

logger = logging.getLogger(__name__)

ORQUESTRATOR_NODE_NAME = "orquestrator"
orquestrator_agent = create_agent(
    model=fast_llm,  # type: ignore[arg-type]
    system_prompt=PROMPT,
)

orquestrator_agent.ainvoke = log_execution_time(  # type: ignore[assignment]
    orquestrator_agent.ainvoke,  # type: ignore[arg-type]
    logger=logger,
)


async def orquestrator_node(state: GraphState) -> Dict[GraphStateKeys, Any]:
    input_text = state["messages"][-1].content[:500]
    logger.info(
        "Agent called",
        extra={"details": {"name": ORQUESTRATOR_NODE_NAME, "input": input_text}},
    )
    response = await orquestrator_agent.ainvoke(state)  # type: ignore[arg-type]
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
