import re
from datetime import datetime

from beanie.operators import Push, Set
from pymongo import DESCENDING

from app.domain.model.chat_entry import ChatEntry
from app.domain.model.chat_session import ChatSession, ChatSessionSummarized
from app.infrastructure.mongodb.entities.chat_session import (
    ChatSessionDocument,
    ChatSessionSummaryProjection,
)
from app.infrastructure.mongodb.mappers.chat_session_mapper import (
    ChatSessionMapper,
    ChatSessionSummarizedMapper,
)


class BeanieChatSessionRepository:
    async def create(self, session: ChatSession) -> None:
        document = ChatSessionMapper.model_to_document(session)
        await document.insert()

    async def append_entry(
        self,
        session_id: str,
        entry: ChatEntry,
        updated_at: datetime,
    ) -> None:
        document_entry = ChatSessionMapper.model_entry_to_document(entry)
        await ChatSessionDocument.find_one(
            ChatSessionDocument.session_id == session_id
        ).update(
            Push({ChatSessionDocument.entries: document_entry}),
            Set({ChatSessionDocument.updated_at: updated_at}),
        )

    async def find_by_session_id(self, session_id: str) -> ChatSession | None:
        document = await ChatSessionDocument.find_one(
            ChatSessionDocument.session_id == session_id
        )
        if document is None:
            return None
        return ChatSessionMapper.document_to_model(document)

    async def update_summary(
        self,
        session_id: str,
        summary: str,
        updated_at: datetime,
    ) -> None:
        await ChatSessionDocument.find_one(
            ChatSessionDocument.session_id == session_id
        ).update(
            Set(
                {
                    ChatSessionDocument.updated_at: updated_at,
                    ChatSessionDocument.summary: summary,
                }
            )
        )

    async def find_summaries(
        self,
        search: str = "",
        limit: int = 3,
    ) -> list[ChatSessionSummarized]:
        find_filter = {}
        if search:
            find_filter[ChatSessionDocument.summary] = re.compile(
                search,
                re.IGNORECASE,
            )

        documents = await (
            ChatSessionDocument.find(find_filter)
            .project(ChatSessionSummaryProjection)
            .sort(ChatSessionDocument.updated_at, DESCENDING)  # type: ignore[arg-type]
            .limit(limit)
            .to_list()
        )
        return [
            ChatSessionSummarizedMapper.document_to_model(document)
            for document in documents
        ]
