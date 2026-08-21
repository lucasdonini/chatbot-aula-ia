import logging
from typing import Any, ClassVar

from langchain_core.messages import SystemMessage
from langgraph.graph.state import CompiledStateGraph

from app.infrastructure.agents._core.prompting.temporal_context import (
    build_temporal_context,
)
from app.infrastructure.agents._core.schemas.specialist_output import FinancialOutput
from app.infrastructure.agents._core.state import GraphState, GraphStateKeys
from app.infrastructure.execution_time_logger import log_execution_time

from .._core.contracts.agent_factory import AgentFactory
from .._core.contracts.agent_node import AgentNode
from .financial_prompt import PROMPT

logger = logging.getLogger(__name__)


class FinancialAgentNode(AgentNode):
    _agent: CompiledStateGraph
    name: ClassVar[str] = "financial"

    def __init__(self, agent_factory: AgentFactory) -> None:
        self._agent = agent_factory.create(
            system_prompt=PROMPT,
            response_format=FinancialOutput,
        )

    @log_execution_time
    async def __call__(self, state: GraphState) -> dict[GraphStateKeys, Any]:
        input_text = state["messages"][-1].content[:500]
        logger.info(
            "Agent called",
            extra={"details": {"name": self.name, "input": input_text}},
        )
        request_state: GraphState = {
            **state,
            "messages": [
                SystemMessage(content=build_temporal_context()),
                *state["messages"],
            ],
        }
        response = await self._agent.ainvoke(request_state)  # type: ignore[arg-type]
        last = (response.get("messages") or [None])[-1]
        output = last.content[:500] if last and last.content else "(tool call)"
        logger.info(
            "Agent response",
            extra={"details": {"from": self.name, "output": output}},
        )
        return {
            GraphStateKeys.MESSAGES: response.get("messages") or [],
            GraphStateKeys.CALLED_AGENTS: [self.name],
        }
