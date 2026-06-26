import logging
import re
import time
from typing import List

from src.model.chat_session import ChatMessage, ChatSession, ChatSessionSummarized

logger = logging.getLogger(__name__)


class ChatHistoryService:
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
        start_time = time.perf_counter()
        logger.info("Searching history: (search: %s, limit: %s)", search, limit)

        filter = {}
        if search:
            pattern = re.compile(search, re.IGNORECASE)
            filter[ChatSession.summary] = pattern

        result: List[ChatSessionSummarized] = await (
            ChatSession.find(filter)
            .project(ChatSessionSummarized)
            .sort((ChatSession.started_at, 1))
            .to_list()
        )

        end_time = time.perf_counter()
        logger.debug(
            "Returning %s results. Took %s seconds", len(result), end_time - start_time
        )
        return result

    async def fetch_messages(self, session_id: str) -> List[ChatMessage]:
        start_time = time.perf_counter()

        logger.info("Fetching messages from session with id %s", session_id)
        session = await ChatSession.find_one(ChatSession.session_id == session_id)
        messages = session.messages if session else []

        end_time = time.perf_counter()
        logger.debug(
            "Returning %s messages. Tool %s seconds.",
            len(messages),
            end_time - start_time,
        )
        return messages
