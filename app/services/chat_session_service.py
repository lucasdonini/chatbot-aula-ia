from app.application.ports.clock import Clock
from app.application.ports.logger import Logger
from app.application.repositories.chat_session_repository import (
    ChatSessionRepository,
)
from app.domain.model.chat_entry import (
    ChatEntry,
    ChatError,
    ChatMessage,
)
from app.domain.model.chat_session import ChatSession

from .session_summary_service import SessionSummaryService

_active_sessions: dict[str, str] = {}


class ChatSessionService:
    def __init__(
        self,
        service: SessionSummaryService,
        repository: ChatSessionRepository,
        logger: Logger,
        clock: Clock,
    ) -> None:
        self._service = service
        self._repository = repository
        self._logger = logger
        self._clock = clock

    async def init_session(self, session_id: str) -> None:
        now = self._clock.now()
        session = ChatSession(
            session_id=session_id,
            started_at=now,
            updated_at=now,
            summary="",
            entries=[],
        )

        await self._repository.create(session)
        _active_sessions[session_id] = session_id
        self._logger.debug(
            "Session initialized",
            details={"session_id": session_id[:8]},
        )

    def get_active_sessions(self) -> dict[str, str]:
        return _active_sessions.copy()

    async def _save_entry(self, session_id: str, entry: ChatEntry) -> None:
        active_session_id = _active_sessions[session_id]
        await self._repository.append_entry(
            active_session_id,
            entry,
            self._clock.now(),
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
        try:
            name = type(error).__name__
            summary = await self._service.summarize_exception(error)
            entry = ChatError(exception=name, summary=summary)
            await self._save_entry(session_id, entry)
            self._logger.debug(
                "Error saved",
                details={"exception_type": entry.exception},
            )
        except Exception as persistence_error:
            self._logger.exception(
                "Failed to save chat error",
                exception=persistence_error,
                details={"original_exception_type": type(error).__name__},
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

        active_session_id = _active_sessions.get(session_id)
        if active_session_id is None:
            return

        session = await self._repository.find_by_session_id(active_session_id)
        if not session or not session.entries:
            return

        summary = await self._service.summarize_session(session.entries)
        await self._repository.update_summary(
            active_session_id,
            summary,
            self._clock.now(),
        )

        _active_sessions.pop(session_id)
        self._logger.debug(
            "Session finalized",
            details={
                "session_id": session_id[:8],
                "entry_count": len(session.entries),
            },
        )
