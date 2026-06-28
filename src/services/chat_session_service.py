import logging
from datetime import datetime
from typing import Union

from bson import ObjectId
from langchain_core.messages import AIMessage, HumanMessage

from src.model.chat_session import ChatMessage, ChatSession

from .session_summary_service import SessionSummaryService

logger = logging.getLogger(__name__)
_active_sessions: dict[str, ObjectId] = {}


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
            messages=[],
        )

        await session.insert()
        _active_sessions[session_id] = session.id
        logger.debug("User session initialized: %s", session)

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
                "$set": {ChatSession.updated_at: datetime.now()},
            }
        )
        logger.debug("Message saved: %s", message)

    async def finalize_session(self, session_id: str) -> str:
        """
        Finalizes the active session:
            1. Load messages from MongoDB
            2. Generate a summary via LLM
            3. Update document with the summary
            4. Remove session from internal state
        Returns the generated summary or an empty string.
        """

        id = _active_sessions.get(session_id)
        if id is None:
            return ""

        session = await ChatSession.find_one(ChatSession.id == id)
        if not session or not session.messages:
            return ""

        summary = await self._service.sumarize(session.messages)
        await session.update(
            {
                "$set": {
                    ChatSession.updated_at: datetime.now(),
                    ChatSession.summary: summary,
                }
            }
        )

        _active_sessions.pop(session_id)
        logger.debug("Session finalized: %s", session)
        return summary
