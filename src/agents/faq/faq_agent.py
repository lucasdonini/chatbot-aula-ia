import logging
from typing import Any, Dict

from langchain.agents import create_agent

from src.infrastructure.execution_time_logger import log_execution_time
from src.model.graph_state import GraphState, GraphStateKeys

from ..llms import fast_llm
from .faq_prompt import FAQ_NODE_NAME, PROMPT
from .tools import TOOLS

logger = logging.getLogger(__name__)

faq_agent = create_agent(model=fast_llm, system_prompt=PROMPT, tools=TOOLS)
faq_agent.ainvoke = log_execution_time(faq_agent.ainvoke, logger=logger)


async def faq_node(state: GraphState) -> Dict[GraphStateKeys, Any]:
    logger.debug("FAQ specialist called. State: %s", state)
    response = await faq_agent.ainvoke(state)
    return {
        GraphStateKeys.MESSAGES: response.get("messages") or [],
        GraphStateKeys.CALLED_AGENTS: [FAQ_NODE_NAME],
    }
