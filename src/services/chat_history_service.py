import logging
import re
from typing import List

from pymongo import DESCENDING

from src.infrastructure.execution_time_logger import log_execution_time
from src.model.chat_session import ChatEntry, ChatSession, ChatSessionSummarized

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
            filter[ChatSession.summary] = pattern

        return await (
            ChatSession.find(filter)
            .project(ChatSessionSummarized)
            .sort(ChatSession.updated_at, DESCENDING)  # type: ignore[arg-type]
            .limit(limit)
            .to_list()
        )

    @log_execution_time
    async def fetch_entries(self, session_id: str) -> List[ChatEntry]:
        logger.debug(
            "Fetching entries",
            extra={"details": {"session_id": session_id[:8]}},
        )
        session = await ChatSession.find_one(ChatSession.session_id == session_id)
        entries = session.entries if session else []

        logger.debug(
            "Entries fetched",
            extra={"details": {"count": len(entries)}},
        )
        return entries
