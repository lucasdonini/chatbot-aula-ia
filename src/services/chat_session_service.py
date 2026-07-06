import logging
from datetime import datetime
from typing import Literal, Union

from beanie import PydanticObjectId
from langchain_core.messages import AIMessage, HumanMessage

from src.model.chat_session import ChatMessage, ChatSession

from .session_summary_service import SessionSummaryService

logger = logging.getLogger(__name__)
_active_sessions: dict[str, PydanticObjectId] = {}


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
        assert session.id is not None
        _active_sessions[session_id] = session.id
        logger.debug(
            "Session initialized",
            extra={"details": {"session_id": session_id[:8]}},
        )

    def get_active_sessions(self) -> dict[str, PydanticObjectId]:
        return _active_sessions.copy()

    async def save_message(
        self, session_id: str, message: Union[AIMessage, HumanMessage]
    ) -> None:
        id = _active_sessions[session_id]
        role: Literal["human", "assistant"] = (
            "human" if isinstance(message, HumanMessage) else "assistant"
        )
        if not isinstance((content := message.content), str):
            raise TypeError(
                f"Received message with non-text content: {type(content).__name__!r}"
            )

        await ChatSession.find_one(ChatSession.id == id).update(
            {
                "$push": {
                    ChatSession.messages: ChatMessage(role=role, content=content)
                },
                "$set": {ChatSession.updated_at: datetime.now()},
            }
        )
        logger.debug(
            "Message saved",
            extra={"details": {"role": role, "content": content[:100]}},
        )

    async def finalize_session(self, session_id: str) -> None:
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
            return

        session = await ChatSession.find_one(ChatSession.id == id)
        if not session or not session.messages:
            return

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
        logger.debug(
            "Session finalized",
            extra={
                "details": {
                    "session_id": session_id[:8],
                    "message_count": len(session.messages),
                }
            },
        )
