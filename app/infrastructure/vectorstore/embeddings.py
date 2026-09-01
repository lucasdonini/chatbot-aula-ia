from langchain_google_genai import GoogleGenerativeAIEmbeddings

from ..settings import settings


class QDrantEmbeddings:
    def __init__(self) -> None:
        self._embeddings = GoogleGenerativeAIEmbeddings(
            model="gemini-embedding-2-preview",
            api_key=settings.gemini_api_key,
        )

    def generate(self, text: str) -> list[float]:
        return self._embeddings.embed_query(
            text, output_dimensionality=settings.embedding_dimmensions
        )

    def generate_batch(self, batch: list[str]) -> list[list[float]]:
        return self._embeddings.embed_documents(
            batch,
            output_dimensionality=settings.embedding_dimmensions,
        )


qdrant_embeddings = QDrantEmbeddings()
