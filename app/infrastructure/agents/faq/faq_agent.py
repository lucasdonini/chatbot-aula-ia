import logging
from typing import Any, ClassVar

from langgraph.graph.state import CompiledStateGraph

from app.infrastructure.agents._core.state import GraphState, GraphStateKeys
from app.infrastructure.execution_time_logger import log_execution_time

from .._core.contracts.agent_factory import AgentFactory
from .._core.contracts.agent_node import AgentNode
from .faq_prompt import FAQ_NODE_NAME, PROMPT

logger = logging.getLogger(__name__)


class FAQAgentNode(AgentNode):
    _agent: CompiledStateGraph
    name: ClassVar[str] = FAQ_NODE_NAME

    def __init__(self, agent_factory: AgentFactory) -> None:
        self._agent = agent_factory.create(system_prompt=PROMPT)

    @log_execution_time
    async def __call__(self, state: GraphState) -> dict[GraphStateKeys, Any]:
        input_text = state["messages"][-1].content[:500]
        logger.info(
            "Agent called",
            extra={"details": {"name": self.name, "input": input_text}},
        )
        response = await self._agent.ainvoke(state)  # type: ignore[arg-type]
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
