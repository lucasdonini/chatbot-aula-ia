from datetime import datetime
from enum import Enum
from typing import Annotated, List, Literal, Optional, Union

from beanie import Document, Indexed
from pydantic import BaseModel, Field


class ChatMessageRole(str, Enum):
    HUMAN = "human"
    ASSISTANT = "assistant"


class ChatMessage(BaseModel):
    type: Literal["message"] = "message"
    role: ChatMessageRole
    content: str


class ChatError(BaseModel):
    type: Literal["error"] = "error"
    exception: str
    summary: str


ChatEntry = Annotated[Union[ChatMessage, ChatError], Field(discriminator="type")]


class ChatSession(Document):
    """ORM for mongodb collection"""

    session_id: Annotated[str, Indexed(unique=True)]
    started_at: Annotated[datetime, Indexed()]
    updated_at: Optional[datetime] = None
    summary: Optional[str] = None
    entries: List[ChatEntry]

    class Settings:
        name = "sessions"


class ChatSessionSummarized(BaseModel):
    """Beanie projection"""

    session_id: str
    summary: Optional[str]
    started_at: datetime
