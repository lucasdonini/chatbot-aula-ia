from typing import Protocol, runtime_checkable

from app.domain.model.chat_entry import AssistantMessage, HumanMessage


@runtime_checkable
class AgentGraph(Protocol):
    async def execute_agent_flux(
        self, message: HumanMessage, session_id: str
    ) -> AssistantMessage: ...
