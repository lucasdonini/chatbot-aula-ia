# ruff: noqa: E501

import logging
import time
from typing import Any, Dict

from langchain.agents import create_agent

from src.model.graph_state import GraphState, GraphStateKeys

from ..llms import fast_llm
from .orquestrator_prompt import PROMPT

logger = logging.getLogger(__name__)

ORQUESTRATOR_NODE_NAME = "orquestrator"
orquestrator_agent = create_agent(model=fast_llm, system_prompt=PROMPT)


async def orquestrator_node(state: GraphState) -> Dict[GraphStateKeys, Any]:
    start_time = time.perf_counter()
    logger.info("Orquestrator called. State: %s", state)
    response = await orquestrator_agent.ainvoke(state)
    end_time = time.perf_counter()
    logger.info("Orquestrator node finished. Time: %s", end_time - start_time)
    return {
        GraphStateKeys.MESSAGES: response.get("messages") or [],
        GraphStateKeys.CALLED_AGENTS: [ORQUESTRATOR_NODE_NAME],
    }
