import logging
import re
from typing import List

from src.infrastructure.execution_time_logger import log_execution_time
from src.model.chat_session import ChatMessage, ChatSession, ChatSessionSummarized

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
        messages are NOT included here—use recuperar_mensagens(doc_id) for that.

        search      : optional term to filter relevant summaries
        limit     : maximum number of sessions returned (most recent first)
        """
        logger.debug("Searching history: (search: %s, limit: %s)", search, limit)

        filter = {}
        if search:
            pattern = re.compile(search, re.IGNORECASE)
            filter[ChatSession.summary] = pattern

        return await (
            ChatSession.find(filter)
            .project(ChatSessionSummarized)
            .sort(ChatSession.started_at)  # type: ignore[arg-type]
            .to_list()
        )

    @log_execution_time
    async def fetch_messages(self, session_id: str) -> List[ChatMessage]:
        logger.debug("Fetching messages from session with id %s", session_id)
        session = await ChatSession.find_one(ChatSession.session_id == session_id)
        messages = session.messages if session else []

        logger.debug(
            "Returning %s messages.",
            len(messages),
        )
        return messages
