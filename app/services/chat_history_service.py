from app.application.ports.logger import Logger
from app.application.repositories.chat_session_repository import (
    ChatSessionRepository,
)
from app.domain.model.chat_entry import ChatEntry
from app.domain.model.chat_session import ChatSessionSummarized


class ChatHistoryService:
    def __init__(self, repository: ChatSessionRepository, logger: Logger) -> None:
        self._repository = repository
        self._logger = logger

    async def fetch_history(
        self, search: str = "", limit: int = 3
    ) -> list[ChatSessionSummarized]:
        """
        Retrieves summaries of PREVIOUS (already concluded) sessions for a user.

        Strategy: first checks the summaries. If a search term is provided,
        filters by it; otherwise, returns the most recent sessions. Full
        messages are NOT included here.

        search      : optional term to filter relevant summaries
        limit       : maximum number of sessions returned (most recent first)
        """
        self._logger.debug(
            "Fetching history",
            details={"search_length": len(search), "limit": limit},
        )

        return await self._repository.find_summaries(search=search, limit=limit)

    async def fetch_entries(self, session_id: str) -> tuple[ChatEntry, ...]:
        self._logger.debug(
            "Fetching entries",
            details={"session_id": session_id[:8]},
        )
        session = await self._repository.find_by_session_id(session_id)
        entries = session.entries if session else tuple()

        self._logger.debug(
            "Entries fetched",
            details={"count": len(entries)},
        )
        return entries
