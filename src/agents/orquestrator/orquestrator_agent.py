# ruff: noqa: E501

import logging
from typing import Any, Dict

from langchain.agents import create_agent

from src.model.graph_state import GraphState, GraphStateKeys

from ..llms import fast_llm
from .orquestrator_prompt import PROMPT

logger = logging.getLogger(__name__)

ORQUESTRATOR_NODE_NAME = "orquestrator"
orquestrator_agent = create_agent(model=fast_llm, system_prompt=PROMPT)


async def orquestrator_node(state: GraphState) -> Dict[GraphStateKeys, Any]:
    logger.info("Orquestrator called. State: %s", state)
    response = await orquestrator_agent.ainvoke(state)
    return {
        GraphStateKeys.MESSAGES: response.get("messages") or [],
        GraphStateKeys.CALLED_AGENTS: [ORQUESTRATOR_NODE_NAME],
    }
