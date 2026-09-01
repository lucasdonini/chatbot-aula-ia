from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from app.infrastructure.vectorstore.repositories.faq_embedding_repository import (
    QDrantFaqSearch,
)


def test_returns_only_faq_payload_contents(
    mock_logger_factory: MagicMock,
) -> None:
    query_response = SimpleNamespace(
        points=[
            SimpleNamespace(payload={"page_content": "Primeiro trecho"}),
            SimpleNamespace(payload={"page_content": "Segundo trecho"}),
        ]
    )

    with (
        patch(
            "app.infrastructure.vectorstore.repositories."
            "faq_embedding_repository.qdrant_embeddings.generate",
            return_value=[0.1, 0.2],
        ) as generate,
        patch(
            "app.infrastructure.vectorstore.repositories."
            "faq_embedding_repository.qdrant_client.query_points",
            return_value=query_response,
        ) as query_points,
    ):
        result = QDrantFaqSearch(logger_factory=mock_logger_factory).search(
            "pergunta", limit=2
        )

    assert result == ["Primeiro trecho", "Segundo trecho"]
    generate.assert_called_once_with("pergunta")
    query_points.assert_called_once_with(
        collection_name="faq-current",
        query=[0.1, 0.2],
        limit=2,
        with_payload=["page_content"],
    )


def test_returns_empty_list_when_qdrant_finds_no_points(
    mock_logger_factory: MagicMock,
) -> None:
    query_response = SimpleNamespace(points=[])

    with (
        patch(
            "app.infrastructure.vectorstore.repositories."
            "faq_embedding_repository.qdrant_embeddings.generate",
            return_value=[0.1, 0.2],
        ),
        patch(
            "app.infrastructure.vectorstore.repositories."
            "faq_embedding_repository.qdrant_client.query_points",
            return_value=query_response,
        ),
    ):
        result = QDrantFaqSearch(logger_factory=mock_logger_factory).search(
            "pergunta", limit=2
        )

    assert result == []


def test_ignores_non_string_faq_payload_content(
    mock_logger_factory: MagicMock,
) -> None:
    query_response = SimpleNamespace(
        points=[
            SimpleNamespace(payload=None),
            SimpleNamespace(payload={}),
            SimpleNamespace(payload={"page_content": 1}),
            SimpleNamespace(payload={"page_content": "Trecho válido"}),
        ]
    )

    with (
        patch(
            "app.infrastructure.vectorstore.repositories."
            "faq_embedding_repository.qdrant_embeddings.generate",
            return_value=[0.1, 0.2],
        ),
        patch(
            "app.infrastructure.vectorstore.repositories."
            "faq_embedding_repository.qdrant_client.query_points",
            return_value=query_response,
        ),
    ):
        result = QDrantFaqSearch(logger_factory=mock_logger_factory).search(
            "pergunta", limit=4
        )

    assert result == ["Trecho válido"]
