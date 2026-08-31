from dataclasses import dataclass

from app.domain.model.chat_entry import AssistantMessage


@dataclass(frozen=True, slots=True)
class AgentExecutionResult:
    message: AssistantMessage
    called_agents: tuple[str, ...]
