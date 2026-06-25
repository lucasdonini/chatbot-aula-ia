# ruff: noqa: E501

import logging
import time
from typing import Any, Dict

from langchain.agents import create_agent

from src.model.graph_state import GraphState, GraphStateKeys

from ..llms import specialist_llm
from .agenda_prompt import AGENDA_NODE_NAME, PROMPT

logger = logging.getLogger(__name__)

agenda_agent = create_agent(model=specialist_llm, system_prompt=PROMPT)


async def agenda_node(state: GraphState) -> Dict[GraphStateKeys, Any]:
    start_time = time.perf_counter()
    logger.info("Agenda specialist called. State: %s", state)
    response = await agenda_agent.ainvoke(state)
    end_time = time.perf_counter()
    logger.info("Agenda node finished. Time: %s", end_time - start_time)
    return {
        GraphStateKeys.MESSAGES: response.get("messages") or [],
        GraphStateKeys.CALLED_AGENTS: [AGENDA_NODE_NAME],
    }
