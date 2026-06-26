import logging
from typing import Any, Dict

from langchain.agents import create_agent

from src.infrastructure.execution_time_logger import log_execution_time
from src.model.graph_state import GraphState, GraphStateKeys

from ..llms import specialist_llm
from .agenda_prompt import AGENDA_NODE_NAME, PROMPT

logger = logging.getLogger(__name__)

agenda_agent = create_agent(model=specialist_llm, system_prompt=PROMPT)
agenda_agent.ainvoke = log_execution_time(agenda_agent.ainvoke, logger=logger)


async def agenda_node(state: GraphState) -> Dict[GraphStateKeys, Any]:
    logger.info("Agenda specialist called. State: %s", state)
    response = await agenda_agent.ainvoke(state)
    return {
        GraphStateKeys.MESSAGES: response.get("messages") or [],
        GraphStateKeys.CALLED_AGENTS: [AGENDA_NODE_NAME],
    }
