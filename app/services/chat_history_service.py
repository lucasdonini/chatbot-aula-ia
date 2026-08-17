import logging
import re
from typing import List

from pymongo import DESCENDING

from app.domain.model.chat_entry import ChatEntry
from app.domain.model.chat_session import ChatSessionSummarized
from app.infrastructure.execution_time_logger import log_execution_time
from app.infrastructure.mongodb.entities.chat_session import (
    ChatSessionDocument,
    ChatSessionSummaryProjection,
)

logger = logging.getLogger(__name__)


class ChatHistoryService:
    @log_execution_time
    async def fetch_history(
        self, search: str = "", limit: int = 3
    ) -> List[ChatSessionSummarized]:
        """
        Retrieves summaries of PREVIOUS (already concluded) sessions for a user.

        Strategy: first checks the summaries. If a search term is provided,
        filters by it; otherwise, returns the most recent sessions. Full
        messages are NOT included here.

        search      : optional term to filter relevant summaries
        limit       : maximum number of sessions returned (most recent first)
        """
        logger.debug(
            "Fetching history",
            extra={"details": {"search": search, "limit": limit}},
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
        return [s.to_model() for s in sessions]

    @log_execution_time
    async def fetch_entries(self, session_id: str) -> List[ChatEntry]:
        logger.debug(
            "Fetching entries",
            extra={"details": {"session_id": session_id[:8]}},
        )
        session = await ChatSessionDocument.find_one(
            ChatSessionDocument.session_id == session_id
        )
        entries = session.entries if session else []

        logger.debug(
            "Entries fetched",
            extra={"details": {"count": len(entries)}},
        )
        return entries
