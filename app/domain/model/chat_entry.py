from dataclasses import dataclass
from enum import Enum
from typing import Literal


class ChatMessageRole(str, Enum):
    HUMAN = "human"
    ASSISTANT = "assistant"


@dataclass(slots=True, frozen=True)
class ChatMessage:
    role: ChatMessageRole
    content: str
    type: Literal["message"] = "message"


@dataclass(slots=True, frozen=True)
class ChatError:
    exception: str
    summary: str
    type: Literal["error"] = "error"


ChatEntry = ChatMessage | ChatError
