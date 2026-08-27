from __future__ import annotations

from dataclasses import asdict

from app.domain.model.chat_entry import (
    AssistantMessage,
    ChatEntry,
    ChatError,
    ChatMessage,
    ChatMessageRole,
    HumanMessage,
)
from app.domain.model.chat_session import ChatSession, ChatSessionSummarized

from ..entities.chat_session import (
    ChatEntryDocument,
    ChatErrorDocument,
    ChatMessageDocument,
    ChatSessionDocument,
    ChatSessionSummaryProjection,
)


class ChatSessionMapper:
    @staticmethod
    def model_entry_to_document(entry: ChatEntry) -> ChatEntryDocument:
        if isinstance(entry, ChatError):
            return ChatErrorDocument(**asdict(entry))

        if isinstance(entry, ChatMessage):
            return ChatMessageDocument(**asdict(entry), role=entry.role)

        raise TypeError(
            "Chat entry submitted to mongodb does not have a recognized "
            f"structure: {entry}"
        )

    @staticmethod
    def document_entry_to_model(entry: ChatEntryDocument) -> ChatEntry:
        if isinstance(entry, ChatErrorDocument):
            return ChatError(**entry.model_dump(exclude={"id"}))

        if isinstance(entry, ChatMessageDocument):
            if entry.role == ChatMessageRole.HUMAN:
                return HumanMessage(content=entry.content)
            if entry.role == ChatMessageRole.ASSISTANT:
                return AssistantMessage(content=entry.content)

        raise TypeError(
            "Chat entry retrieved from MongoDB does not have a recognized "
            f"structure: {entry}"
        )

    @staticmethod
    def model_to_document(model: ChatSession) -> ChatSessionDocument:
        data = asdict(model)
        data.pop("entries")

        return ChatSessionDocument(
            **data,
            entries=[
                ChatSessionMapper.model_entry_to_document(e) for e in model.entries
            ],
        )

    @staticmethod
    def document_to_model(document: ChatSessionDocument) -> ChatSession:
        return ChatSession(
            **document.model_dump(exclude={"id", "entries"}),
            entries=tuple(
                ChatSessionMapper.document_entry_to_model(e) for e in document.entries
            ),
        )


class ChatSessionSummarizedMapper:
    @staticmethod
    def document_to_model(
        document: ChatSessionSummaryProjection,
    ) -> ChatSessionSummarized:
        return ChatSessionSummarized(**document.model_dump(exclude={"id"}))
