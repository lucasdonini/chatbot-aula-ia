import copy
import logging
from typing import Any, Dict, List, Set

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, AnyMessage, ToolMessage

from src.infrastructure.execution_time_logger import log_execution_time
from src.model.graph_state import GraphState, GraphStateKeys
from src.services.chat_history_service import ChatHistoryService

from ..llms import fast_llm
from .router_prompt import PROMPT
from .tools import SearchHistoryTool

logger = logging.getLogger(__name__)

history_service = ChatHistoryService()
history_tool = SearchHistoryTool(service=history_service)

TOOLS = [history_tool]

ROUTER_NODE_NAME = "router"
router_agent = create_agent(
    model=fast_llm,
    system_prompt=PROMPT,
    tools=TOOLS,
)

router_agent.ainvoke = log_execution_time(router_agent.ainvoke, logger=logger)


def _filter_messages_for_router(messages: List[AnyMessage]) -> List[AnyMessage]:
    """
    Remove tool calls/results from other agents so that
    the router does not think he has access to them.
    """
    allowed_tools = {t.name for t in TOOLS}
    tool_ids_to_skip: Set[str] = set()
    filtered: List[AnyMessage] = []

    for msg in messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            msg = copy.deepcopy(msg)
            for tc in msg.tool_calls:
                if tc["name"] not in allowed_tools:
                    tool_ids_to_skip.add(tc["id"])
            msg.tool_calls = [
                tc for tc in msg.tool_calls if tc["name"] in allowed_tools
            ]
            msg.invalid_tool_calls = []

        if isinstance(msg, ToolMessage) and msg.tool_call_id in tool_ids_to_skip:
            continue

        filtered.append(msg)

    return filtered


async def router_node(state: GraphState) -> Dict[GraphStateKeys, Any]:
    logger.info("Router called. State: %s", state)
    logger.debug("Filtering state to avoid confusions about tools...")
    filtered_state = {
        **state,
        "messages": _filter_messages_for_router(state["messages"]),
    }
    logger.debug("Filtered state: %s", filtered_state)
    response = await router_agent.ainvoke(filtered_state)
    return {
        GraphStateKeys.MESSAGES: response.get("messages") or [],
        GraphStateKeys.CALLED_AGENTS: [ROUTER_NODE_NAME],
    }
