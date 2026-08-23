from typing import Any, ClassVar

from langgraph.graph.state import CompiledStateGraph

from app.application.ports.logger import Logger
from app.infrastructure.agents._core.state import GraphState, GraphStateKeys

from .._core.contracts.agent_factory import AgentFactory
from .._core.contracts.agent_node import AgentNode
from .faq_prompt import FAQ_NODE_NAME, PROMPT


class FAQAgentNode(AgentNode):
    _agent: CompiledStateGraph
    name: ClassVar[str] = FAQ_NODE_NAME

    def __init__(self, agent_factory: AgentFactory, logger: Logger) -> None:
        self._logger = logger
        self._agent = agent_factory.create(system_prompt=PROMPT)

    async def __call__(self, state: GraphState) -> dict[GraphStateKeys, Any]:
        input_length = len(state["messages"][-1].content)
        self._logger.info(
            "Agent called",
            details={"name": self.name, "input_length": input_length},
        )
        response = await self._agent.ainvoke(state)  # type: ignore[arg-type]
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
