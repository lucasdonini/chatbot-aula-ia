# ruff: noqa: E501

import logging
import time
from typing import Any, Dict

from langchain.agents import create_agent

from src.model.graph_state import GraphState, GraphStateKeys

from ..llms import fast_llm
from .faq_prompt import FAQ_NODE_NAME, PROMPT
from .tools import TOOLS

logger = logging.getLogger(__name__)

faq_agent = create_agent(model=fast_llm, system_prompt=PROMPT, tools=TOOLS)


async def faq_node(state: GraphState) -> Dict[GraphStateKeys, Any]:
    start_time = time.perf_counter()
    logger.debug("FAQ specialist called. State: %s", state)
    response = await faq_agent.ainvoke(state)
    end_time = time.perf_counter()
    logger.info("FAQ node finished. Time: %s", end_time - start_time)
    return {
        GraphStateKeys.MESSAGES: response.get("messages") or [],
        GraphStateKeys.CALLED_AGENTS: [FAQ_NODE_NAME],
    }
