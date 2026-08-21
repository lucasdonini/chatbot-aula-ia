import copy
import json
import logging
from collections.abc import Collection, Sequence
from typing import Any, ClassVar, cast

from langchain_core.messages import AIMessage, AnyMessage, SystemMessage, ToolMessage
from langgraph.graph.state import CompiledStateGraph

from app.infrastructure.execution_time_logger import log_execution_time

from .._core.contracts.agent_factory import AgentFactory
from .._core.contracts.agent_node import AgentNode
from .._core.prompting.temporal_context import build_temporal_context
from .._core.specialist import SpecialistRegistration
from .._core.state import GraphState, GraphStateKeys
from .router_prompt import build_router_prompt

logger = logging.getLogger(__name__)

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


def _filter_messages_for_router(
    messages: list[AnyMessage],
    allowed_tool_names: Collection[str],
) -> list[AnyMessage]:
    tool_ids_to_skip: set[str] = set()
    filtered: list[AnyMessage] = []

    for msg in messages:
        if isinstance(msg, AIMessage) and msg.tool_calls:
            foreign_ids = {
                cast(str, tool_call["id"])
                for tool_call in msg.tool_calls
                if tool_call["name"] not in allowed_tool_names and tool_call.get("id")
            }
            tool_ids_to_skip.update(foreign_ids)

            own_calls = [
                tool_call
                for tool_call in msg.tool_calls
                if tool_call["name"] in allowed_tool_names
            ]
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


class RouterAgentNode(AgentNode):
    _agent: CompiledStateGraph
    name: ClassVar[str] = "router"

    def __init__(
        self,
        *,
        agent_factory: AgentFactory,
        specialists: Sequence[SpecialistRegistration],
        allowed_tool_names: Collection[str],
    ) -> None:
        self._allowed_tool_names = frozenset(allowed_tool_names)
        self._agent = agent_factory.create(
            system_prompt=build_router_prompt(specialists)
        )

    @log_execution_time
    async def __call__(self, state: GraphState) -> dict[GraphStateKeys, Any]:
        input_text = state["messages"][-1].content[:500]
        logger.info(
            "Agent called",
            extra={"details": {"name": self.name, "input": input_text}},
        )
        filtered_state: GraphState = {
            **state,
            "messages": [
                SystemMessage(content=build_temporal_context()),
                *_filter_messages_for_router(
                    state["messages"],
                    self._allowed_tool_names,
                ),
            ],
        }
        response = await self._agent.ainvoke(filtered_state)  # type: ignore[arg-type]
        output = (
            response["messages"][-1].content[:500] if response.get("messages") else ""
        )
        logger.info(
            "Agent response",
            extra={
                "details": {
                    "from": self.name,
                    "output": output or "(tool call)",
                }
            },
        )
        return {
            GraphStateKeys.MESSAGES: response.get("messages") or [],
            GraphStateKeys.CALLED_AGENTS: [self.name],
        }
