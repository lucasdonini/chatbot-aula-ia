import re

from pymongo import DESCENDING

from app.application.ports.logger import Logger
from app.domain.model.chat_entry import ChatEntry
from app.domain.model.chat_session import ChatSessionSummarized
from app.infrastructure.mongodb.entities.chat_session import (
    ChatSessionDocument,
    ChatSessionSummaryProjection,
)
from app.infrastructure.mongodb.mappers.chat_session_mapper import (
    ChatSessionMapper,
    ChatSessionSummarizedMapper,
)


class ChatHistoryService:
    def __init__(self, logger: Logger) -> None:
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

        filter = {}
        if search:
            pattern = re.compile(search, re.IGNORECASE)
            filter[ChatSessionDocument.summary] = pattern

        sessions = await (
            ChatSessionDocument.find(filter)
            .project(ChatSessionSummaryProjection)
            .sort(ChatSessionDocument.updated_at, DESCENDING)  # type: ignore[arg-type]
            .limit(limit)
            .to_list()
        )
        return [ChatSessionSummarizedMapper.document_to_model(s) for s in sessions]

    async def fetch_entries(self, session_id: str) -> list[ChatEntry]:
        self._logger.debug(
            "Fetching entries",
            details={"session_id": session_id[:8]},
        )
        session = await ChatSessionDocument.find_one(
            ChatSessionDocument.session_id == session_id
        )
        entries = session.entries if session else []

        self._logger.debug(
            "Entries fetched",
            details={"count": len(entries)},
        )
        return [ChatSessionMapper.document_entry_to_model(e) for e in entries]
