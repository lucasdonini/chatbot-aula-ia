from beanie import PydanticObjectId
from beanie.operators import Push, Set

from app.application.ports.clock import Clock
from app.application.ports.logger import Logger
from app.domain.model.chat_entry import (
    ChatEntry,
    ChatError,
    ChatMessage,
)
from app.infrastructure.mongodb.entities.chat_session import ChatSessionDocument
from app.infrastructure.mongodb.mappers.chat_session_mapper import ChatSessionMapper

from .session_summary_service import SessionSummaryService

_active_sessions: dict[str, PydanticObjectId] = {}


class ChatSessionService:
    def __init__(
        self,
        service: SessionSummaryService,
        logger: Logger,
        clock: Clock,
    ) -> None:
        self._service = service
        self._logger = logger
        self._clock = clock

    async def init_session(self, session_id: str) -> None:
        now = self._clock.now()
        session = ChatSessionDocument(
            session_id=session_id,
            started_at=now,
            updated_at=now,
            summary="",
            entries=[],
        )

        await session.insert()
        assert session.id is not None
        _active_sessions[session_id] = session.id
        self._logger.debug(
            "Session initialized",
            details={"session_id": session_id[:8]},
        )

    def get_active_sessions(self) -> dict[str, PydanticObjectId]:
        return _active_sessions.copy()

    async def _save_entry(self, session_id: str, entry: ChatEntry) -> None:
        doc_id = _active_sessions[session_id]
        doc_entry = ChatSessionMapper.model_entry_to_document(entry)
        await ChatSessionDocument.find_one(ChatSessionDocument.id == doc_id).update(
            Push({ChatSessionDocument.entries: doc_entry}),
            Set({ChatSessionDocument.updated_at: self._clock.now()}),
        )

    async def save_message(self, session_id: str, message: ChatMessage) -> None:
        await self._save_entry(session_id, message)
        self._logger.debug(
            "Message saved",
            details={
                "role": message.role.value,
                "content_length": len(message.content),
            },
        )

    async def save_error(self, session_id: str, error: Exception) -> None:
        name = type(error).__name__
        summary = await self._service.summarize_exception(error)
        entry = ChatError(exception=name, summary=summary)
        await self._save_entry(session_id, entry)
        self._logger.debug(
            "Error saved",
            details={"exception_type": entry.exception},
        )

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

        session = await ChatSessionDocument.find_one(ChatSessionDocument.id == id)
        if not session or not session.entries:
            return

        entries = [
            ChatSessionMapper.document_entry_to_model(e) for e in session.entries
        ]
        summary = await self._service.summarize_session(entries)
        await session.update(
            Set(
                {
                    ChatSessionDocument.updated_at: self._clock.now(),
                    ChatSessionDocument.summary: summary,
                }
            )
        )

        _active_sessions.pop(session_id)
        self._logger.debug(
            "Session finalized",
            details={
                "session_id": session_id[:8],
                "entry_count": len(session.entries),
            },
        )
