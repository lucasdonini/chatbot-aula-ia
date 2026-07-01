import copy
import json
import logging
from typing import Any, Dict, List, Set, cast

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
    model=fast_llm,  # type: ignore[arg-type]
    system_prompt=PROMPT,
    tools=TOOLS,
)

router_agent.ainvoke = log_execution_time(  # type: ignore[assignment]
    router_agent.ainvoke,  # type: ignore[arg-type]
    logger=logger,
)


SPECIALIST_JSON_KEYS = {"dominio"}


def _is_specialist_json(content: Any) -> bool:
    if not isinstance(content, str):
        return False
    text = content.strip()
    if not (text.startswith("{") and text.endswith("}")):
        return False
    try:
        data = json.loads(text)
    except json.JSONDecodeError:
        return False
    return isinstance(data, dict) and bool(SPECIALIST_JSON_KEYS & data.keys())


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
            foreign_ids = {
                cast(str, tc["id"])
                for tc in msg.tool_calls
                if tc["name"] not in allowed_tools and tc.get("id")
            }
            if foreign_ids:
                tool_ids_to_skip.update(foreign_ids)

            own_calls = [tc for tc in msg.tool_calls if tc["name"] in allowed_tools]
            if not own_calls:
                continue

            msg = copy.deepcopy(msg)
            msg.tool_calls = own_calls
            msg.invalid_tool_calls = []
            filtered.append(msg)
            continue

        if isinstance(msg, ToolMessage):
            if msg.tool_call_id not in tool_ids_to_skip:
                filtered.append(msg)
            continue

        if isinstance(msg, AIMessage):
            if not _is_specialist_json(msg.content):
                filtered.append(msg)
            continue

        filtered.append(msg)

    return filtered


async def router_node(state: GraphState) -> Dict[GraphStateKeys, Any]:
    logger.info("─" * 50)
    logger.info(" [NODE] ROUTER ")
    logger.info(" Input: %s", state["messages"][-1].content[:500])
    filtered_state = {
        **state,
        "messages": _filter_messages_for_router(state["messages"]),
    }
    response = await router_agent.ainvoke(filtered_state)  # type: ignore[call-overload]
    output = response["messages"][-1].content[:500] if response.get("messages") else ""
    logger.info(" Output: %s", output or "(tool call)")
    logger.info("─" * 50)
    return {
        GraphStateKeys.MESSAGES: response.get("messages") or [],
        GraphStateKeys.CALLED_AGENTS: [ROUTER_NODE_NAME],
    }
