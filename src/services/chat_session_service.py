import logging
from datetime import datetime
from typing import Union

from beanie import PydanticObjectId
from beanie.operators import Push, Set
from langchain_core.messages import AIMessage, HumanMessage

from src.model.chat_session import (
    ChatEntry,
    ChatError,
    ChatMessage,
    ChatMessageRole,
    ChatSession,
)

from .session_summary_service import SessionSummaryService

logger = logging.getLogger(__name__)
_active_sessions: dict[str, PydanticObjectId] = {}


class ChatSessionService:
    def __init__(self, service: SessionSummaryService):
        self._service = service

    async def init_session(self, session_id: str) -> None:
        now = datetime.now()
        session = ChatSession(
            session_id=session_id,
            started_at=now,
            updated_at=now,
            summary="",
            entries=[],
        )

        await session.insert()
        assert session.id is not None
        _active_sessions[session_id] = session.id
        logger.debug(
            "Session initialized",
            extra={"details": {"session_id": session_id[:8]}},
        )

    def get_active_sessions(self) -> dict[str, PydanticObjectId]:
        return _active_sessions.copy()

    async def _save_entry(self, session_id: str, entry: ChatEntry) -> None:
        doc_id = _active_sessions[session_id]
        await ChatSession.find_one(ChatSession.id == doc_id).update(
            Push({ChatSession.entries: entry}),
            Set({ChatSession.updated_at: datetime.now()}),
        )

    async def save_message(
        self, session_id: str, message: Union[AIMessage, HumanMessage]
    ) -> None:
        role = (
            ChatMessageRole.HUMAN
            if isinstance(message, HumanMessage)
            else ChatMessageRole.ASSISTANT
        )
        if not isinstance((content := message.content), str):
            raise TypeError(
                f"Received message with non-text content: {type(content).__name__!r}"
            )

        entry = ChatMessage(role=role, content=content)
        await self._save_entry(session_id, entry)
        logger.debug(
            "Message saved",
            extra={"details": entry.model_dump()},
        )

    async def save_error(self, session_id: str, error: Exception) -> None:
        name = type(error).__name__
        summary = await self._service.summarize_exception(error)
        entry = ChatError(exception=name, summary=summary)
        await self._save_entry(session_id, entry)
        logger.debug("Error saved", extra={"details": entry.model_dump()})

    async def finalize_session(self, session_id: str) -> None:
        """
        Finalizes the active session:
            1. Load entries from MongoDB
            2. Generate a summary via LLM
            3. Update document with the summary
            4. Remove session from internal state
        Returns the generated summary or an empty string.
        """

        id = _active_sessions.get(session_id)
        if id is None:
            return

        session = await ChatSession.find_one(ChatSession.id == id)
        if not session or not session.entries:
            return

        summary = await self._service.summarize_session(session.entries)
        await session.update(
            Set(
                {
                    ChatSession.updated_at: datetime.now(),
                    ChatSession.summary: summary,
                }
            )
        )

        _active_sessions.pop(session_id)
        logger.debug(
            "Session finalized",
            extra={
                "details": {
                    "session_id": session_id[:8],
                    "entry_count": len(session.entries),
                }
            },
        )
