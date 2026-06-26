from datetime import datetime
from typing import Annotated, List, Literal, Optional

from beanie import Document, Indexed
from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: Literal["human", "assistant"]
    content: str


class ChatSession(Document):
    """ORM for mongodb collection"""

    session_id: Annotated[str, Indexed(unique=True)]
    started_at: Annotated[datetime, Indexed()]
    updated_at: Optional[datetime] = None
    summary: Optional[str] = None
    messages: List[ChatMessage]

    class Settings:
        name = "sessions"


class ChatSessionSummarized(BaseModel):
    """Beanie projection"""

    session_id: str
    summary: Optional[str]
    started_at: datetime
