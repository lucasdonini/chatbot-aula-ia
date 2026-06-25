# ruff: noqa: E501

import logging
from typing import Any, Dict

from langchain.agents import create_agent

from src.model.graph_state import GraphState, GraphStateKeys

from ..llms import fast_llm
from .router_prompt import PROMPT

logger = logging.getLogger(__name__)

ROUTER_NODE_NAME = "router"
router_agent = create_agent(model=fast_llm, system_prompt=PROMPT)


async def router_node(state: GraphState) -> Dict[GraphStateKeys, Any]:
    logger.info("Router called. State: %s", state)
    response = await router_agent.ainvoke(state)
    return {
        GraphStateKeys.MESSAGES: response.get("messages") or [],
        GraphStateKeys.CALLED_AGENTS: [ROUTER_NODE_NAME],
    }
