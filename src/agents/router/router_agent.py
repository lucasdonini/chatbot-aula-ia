import logging
from typing import Any, Dict

from langchain.agents import create_agent

from src.infrastructure.execution_time_logger import log_execution_time
from src.model.graph_state import GraphState, GraphStateKeys
from src.services.chat_history_service import ChatHistoryService

from ..llms import fast_llm
from .router_prompt import PROMPT
from .tools import SearchHistoryTool

logger = logging.getLogger(__name__)

history_service = ChatHistoryService()
history_tool = SearchHistoryTool(service=history_service)

ROUTER_NODE_NAME = "router"
router_agent = create_agent(
    model=fast_llm,
    system_prompt=PROMPT,
    tools=[history_tool],
)

router_agent.ainvoke = log_execution_time(router_agent.ainvoke, logger=logger)


async def router_node(state: GraphState) -> Dict[GraphStateKeys, Any]:
    logger.info("Router called. State: %s", state)
    response = await router_agent.ainvoke(state)
    return {
        GraphStateKeys.MESSAGES: response.get("messages") or [],
        GraphStateKeys.CALLED_AGENTS: [ROUTER_NODE_NAME],
    }
