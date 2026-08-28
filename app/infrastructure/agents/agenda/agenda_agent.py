from typing import Any, ClassVar

from langchain_core.messages import SystemMessage
from langgraph.graph.state import CompiledStateGraph

from app.application.ports.clock import Clock
from app.application.ports.logger import Logger, LoggerFactory
from app.infrastructure.agents._core.prompting.temporal_context import (
    build_temporal_context,
)
from app.infrastructure.agents._core.schemas.specialist_output import AgendaOutput
from app.infrastructure.agents._core.state import GraphState, GraphStateKeys

from .._core.contracts.agent_factory import AgentFactory
from .._core.contracts.agent_node import AgentNode
from .agenda_prompt import PROMPT


class AgendaAgentNode(AgentNode):
    _agent: CompiledStateGraph
    _logger: Logger
    _clock: Clock
    name: ClassVar[str] = "agenda"

    def __init__(
        self,
        agent_factory: AgentFactory,
        logger_factory: LoggerFactory,
        clock: Clock,
    ) -> None:
        self._logger = logger_factory(__name__)
        self._clock = clock
        self._agent = agent_factory.create(
            system_prompt=PROMPT,
            response_format=AgendaOutput,
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
                SystemMessage(content=build_temporal_context(self._clock)),
                *state["messages"],
            ],
        }

        # type: ignore[arg-type]
        response = await self._agent.ainvoke(request_state)
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
