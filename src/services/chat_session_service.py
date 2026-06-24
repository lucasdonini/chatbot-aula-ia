import logging
from datetime import datetime, timezone
from typing import Union

from langchain_core.messages import AIMessage, HumanMessage

from src.model.chat_session import ChatMessage, ChatSession

from .session_summary_service import SessionSummaryService

logger = logging.getLogger(__name__)
_active_sessions: dict[str, str] = {}


class ChatSessionService:
    def __init__(self, service: SessionSummaryService):
        self._service = service

    def _now(self) -> datetime:
        return datetime.now(timezone.utc)

    async def init_session(self, session_id: str) -> None:
        now = self._now()
        session = ChatSession(
            session_id=session_id,
            started_at=now,
            updated_at=now,
            summary="",
            messages=[],
        )

        await session.insert()
        _active_sessions[session_id] = str(session.id)
        logger.info("User session initialized: %s", session)

    def get_active_sessions(self) -> dict[str, str]:
        return _active_sessions.copy()

    async def save_message(
        self, session_id: str, message: Union[AIMessage, HumanMessage]
    ) -> None:
        id = _active_sessions[session_id]
        role = "human" if isinstance(message, HumanMessage) else "assistant"
        await ChatSession.find_one(ChatSession.id == id).update(
            {
                "$push": {
                    ChatSession.messages: ChatMessage(
                        role=role, content=message.content
                    )
                },
                "$set": {ChatSession.updated_at: self._now()},
            }
        )
        logger.info("Message saved: %s", message)

    async def finalize_session(self, session_id: str) -> str:
        """
        Finalizes the active session:
            1. Load messages from MongoDB
            2. Generate a summary via LLM
            3. Update document with the summary
            4. Remove session from internal state
        Returns the generated summary or an empty string.
        """

        if id := _active_sessions.get(session_id) is None:
            return ""

        session = await ChatSession.find_one(ChatSession.id == id)
        if not session or not session.messages:
            return ""

        summary = self._service.sumarize(session.messages)
        await session.update(
            {
                "$set": {
                    ChatSession.updated_at: self._now(),
                    ChatSession.summary: summary,
                }
            }
        )

        _active_sessions.pop(session_id)
        logger.info("Session finalized: %s", session)
        return summary
