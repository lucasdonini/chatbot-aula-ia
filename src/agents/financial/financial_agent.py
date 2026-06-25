import logging
import time
from typing import Any, Dict

from langchain.agents import create_agent

from src.model.graph_state import GraphState, GraphStateKeys

from ..llms import specialist_llm
from .financial_prompt import FINANCIAL_NODE_NAME, PROMPT
from .tools import TOOLS

logger = logging.getLogger(__name__)

financial_agent = create_agent(model=specialist_llm, system_prompt=PROMPT, tools=TOOLS)


async def financial_node(state: GraphState) -> Dict[GraphStateKeys, Any]:
    start_time = time.perf_counter()
    logger.info("Financial specialist called. State: %s", state)
    response = await financial_agent.ainvoke(state)
    end_time = time.perf_counter()
    logger.info("Financial node finished. Time: %s", end_time - start_time)
    return {
        GraphStateKeys.MESSAGES: response.get("messages") or [],
        GraphStateKeys.CALLED_AGENTS: [FINANCIAL_NODE_NAME],
    }
