from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Literal


class ChatMessageRole(str, Enum):
    HUMAN = "human"
    ASSISTANT = "assistant"


@dataclass(slots=True, frozen=True)
class ChatMessage(ABC):
    content: str
    type: Literal["message"] = "message"

    @property
    @abstractmethod
    def role(self) -> ChatMessageRole: ...


@dataclass(slots=True, frozen=True)
class HumanMessage(ChatMessage):
    @property
    def role(self) -> ChatMessageRole:
        return ChatMessageRole.HUMAN


@dataclass(slots=True, frozen=True)
class AssistantMessage(ChatMessage):
    @property
    def role(self) -> ChatMessageRole:
        return ChatMessageRole.ASSISTANT


@dataclass(slots=True, frozen=True)
class ChatError:
    exception: str
    summary: str
    type: Literal["error"] = "error"


ChatEntry = ChatMessage | ChatError
