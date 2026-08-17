from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import Annotated

from beanie import Document, Indexed
from pydantic import BaseModel, Field

from app.domain.model.chat_entry import ChatEntry
from app.domain.model.chat_session import ChatSession, ChatSessionSummarized


class ChatSessionDocument(Document):
    """ORM for mongodb collection"""

    session_id: Annotated[str, Indexed(unique=True)]
    started_at: Annotated[datetime, Indexed()]
    updated_at: datetime | None = None
    summary: str | None = None
    entries: list[Annotated[ChatEntry, Field(discriminator="type")]]

    class Settings:
        name = "sessions"

    @classmethod
    def from_model(cls, model: ChatSession) -> ChatSessionDocument:
        return cls(**asdict(model))

    def to_model(self) -> ChatSession:
        return ChatSession(**self.model_dump(exclude={"id"}))


class ChatSessionSummaryProjection(BaseModel):
    """Beanie projection"""

    session_id: str
    summary: str | None
    started_at: datetime

    def to_model(self) -> ChatSessionSummarized:
        return ChatSessionSummarized(**self.model_dump(exclude={"id"}))
