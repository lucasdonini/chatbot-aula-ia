from typing import Any, ClassVar

from langchain_core.messages import SystemMessage
from langgraph.graph.state import CompiledStateGraph

from app.application.ports.logger import Logger
from app.infrastructure.agents._core.prompting.temporal_context import (
    build_temporal_context,
)
from app.infrastructure.agents._core.schemas.specialist_output import FinancialOutput
from app.infrastructure.agents._core.state import GraphState, GraphStateKeys

from .._core.contracts.agent_factory import AgentFactory
from .._core.contracts.agent_node import AgentNode
from .financial_prompt import PROMPT


class FinancialAgentNode(AgentNode):
    _agent: CompiledStateGraph
    name: ClassVar[str] = "financial"

    def __init__(self, agent_factory: AgentFactory, logger: Logger) -> None:
        self._logger = logger
        self._agent = agent_factory.create(
            system_prompt=PROMPT,
            response_format=FinancialOutput,
        )

    async def __call__(self, state: GraphState) -> dict[GraphStateKeys, Any]:
        input_length = len(state["messages"][-1].content)
        self._logger.info(
            "Agent called",
            details={"name": self.name, "input_length": input_length},
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
        output_length = len(last.content) if last and last.content else 0
        self._logger.info(
            "Agent response",
            details={"from": self.name, "output_length": output_length},
        )
        return {
            GraphStateKeys.MESSAGES: response.get("messages") or [],
            GraphStateKeys.CALLED_AGENTS: [self.name],
        }
