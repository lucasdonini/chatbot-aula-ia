from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest
from langchain_core.documents import Document
from qdrant_client import models

from app.infrastructure.vectorstore.ingestors.faq_ingestor import QDrantFaqIngestor


def test_skips_ingestion_when_disabled(mock_logger_factory: MagicMock) -> None:
    with (
        patch(
            "app.infrastructure.vectorstore.ingestors."
            "faq_ingestor.settings.ingest_faq_pdf",
            False,
        ),
        patch(
            "app.infrastructure.vectorstore.ingestors."
            "faq_ingestor.qdrant_client.create_collection"
        ) as create_collection,
    ):
        result = QDrantFaqIngestor(logger_factory=mock_logger_factory).ingest()

    assert result == (False, 0)
    create_collection.assert_not_called()


def test_ingests_chunks_with_expected_payload(
    mock_logger_factory: MagicMock,
) -> None:
    loader = MagicMock()
    loader.load.return_value = [
        Document(
            page_content="Conteúdo do FAQ",
            metadata={
                "page": 3,
                "source": "C:/Users/developer/private/faq.pdf",
            },
        )
    ]
    with (
        patch(
            "app.infrastructure.vectorstore.ingestors.faq_ingestor.PyPDFLoader",
            return_value=loader,
        ),
        patch(
            "app.infrastructure.vectorstore.ingestors."
            "faq_ingestor.settings.ingest_faq_pdf",
            True,
        ),
        patch(
            "app.infrastructure.vectorstore.ingestors.faq_ingestor.qdrant_client"
        ) as client,
        patch(
            "app.infrastructure.vectorstore.ingestors."
            "faq_ingestor.qdrant_embeddings.generate_batch",
            return_value=[[0.1, 0.2]],
        ) as generate_batch,
    ):
        client.create_collection.return_value = True
        client.count.return_value = SimpleNamespace(count=1)
        client.get_aliases.return_value = SimpleNamespace(aliases=[])
        client.update_collection_aliases.return_value = True

        result = QDrantFaqIngestor(logger_factory=mock_logger_factory).ingest()

    assert result == (True, 1)
    client.delete_collection.assert_not_called()
    generate_batch.assert_called_once_with(["Conteúdo do FAQ"])
    client.upsert.assert_called_once()

    collection_name = client.create_collection.call_args.kwargs["collection_name"]
    assert collection_name.startswith("faq-chunks-")
    assert client.upsert.call_args.kwargs["collection_name"] == collection_name
    assert client.upsert.call_args.kwargs["wait"] is True

    point = client.upsert.call_args.kwargs["points"][0]
    assert point.vector == [0.1, 0.2]
    assert point.payload == {
        "page_content": "Conteúdo do FAQ",
        "page_number": 3,
        "source": "FAQ_assessor_v1.1.pdf",
    }

    operations = client.update_collection_aliases.call_args.kwargs[
        "change_aliases_operations"
    ]
    assert len(operations) == 1
    assert isinstance(operations[0], models.CreateAliasOperation)
    assert operations[0].create_alias.alias_name == "faq-current"
    assert operations[0].create_alias.collection_name == collection_name


def test_switches_existing_alias_atomically(
    mock_logger_factory: MagicMock,
) -> None:
    with patch(
        "app.infrastructure.vectorstore.ingestors.faq_ingestor.qdrant_client"
    ) as client:
        client.get_aliases.return_value = SimpleNamespace(
            aliases=[
                SimpleNamespace(
                    alias_name="faq-current",
                    collection_name="faq-chunks-old",
                )
            ]
        )
        client.update_collection_aliases.return_value = True

        previous = QDrantFaqIngestor(
            logger_factory=mock_logger_factory
        )._activate_collection(collection_name="faq-chunks-new")

    assert previous == "faq-chunks-old"
    operations = client.update_collection_aliases.call_args.kwargs[
        "change_aliases_operations"
    ]
    assert len(operations) == 2
    assert isinstance(operations[0], models.DeleteAliasOperation)
    assert operations[0].delete_alias.alias_name == "faq-current"
    assert isinstance(operations[1], models.CreateAliasOperation)
    assert operations[1].create_alias.alias_name == "faq-current"
    assert operations[1].create_alias.collection_name == "faq-chunks-new"
    client.delete_collection.assert_called_once_with(collection_name="faq-chunks-old")


def test_removes_only_new_collection_when_ingestion_fails(
    mock_logger_factory: MagicMock,
) -> None:
    loader = MagicMock()
    loader.load.return_value = [Document(page_content="Conteúdo do FAQ")]

    with (
        patch(
            "app.infrastructure.vectorstore.ingestors.faq_ingestor.PyPDFLoader",
            return_value=loader,
        ),
        patch(
            "app.infrastructure.vectorstore.ingestors."
            "faq_ingestor.settings.ingest_faq_pdf",
            True,
        ),
        patch(
            "app.infrastructure.vectorstore.ingestors.faq_ingestor.qdrant_client"
        ) as client,
        patch(
            "app.infrastructure.vectorstore.ingestors."
            "faq_ingestor.qdrant_embeddings.generate_batch",
            side_effect=RuntimeError("embedding failed"),
        ),
        pytest.raises(RuntimeError, match="embedding failed"),
    ):
        client.create_collection.return_value = True
        QDrantFaqIngestor(logger_factory=mock_logger_factory).ingest()

    collection_name = client.create_collection.call_args.kwargs["collection_name"]
    client.delete_collection.assert_called_once_with(collection_name=collection_name)
    client.update_collection_aliases.assert_not_called()
