from unittest.mock import MagicMock, patch

from langchain_core.documents import Document

from app.infrastructure.faq_search import FaissFaqSearch


def test_returns_only_faq_document_contents() -> None:
    database = MagicMock()
    database.similarity_search.return_value = [
        Document(page_content="Primeiro trecho", metadata={"page": 1}),
        Document(page_content="Segundo trecho", metadata={"page": 2}),
    ]

    with patch("app.infrastructure.faq_search.get_faq_db", return_value=database):
        result = FaissFaqSearch().search("pergunta", limit=2)

    assert result == ["Primeiro trecho", "Segundo trecho"]
    database.similarity_search.assert_called_once_with("pergunta", k=2)
