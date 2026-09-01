import uuid

from langchain_community.document_loaders import PyPDFLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from qdrant_client import models

from app.application.ports.logger import Logger, LoggerFactory
from app.infrastructure.paths import FAQ_PDF
from app.infrastructure.settings import settings

from ..client import qdrant_client
from ..embeddings import qdrant_embeddings


class QDrantFaqIngestor:
    _logger: Logger

    # Pipeline state
    _docs: list[Document]
    _chunks: list[Document]
    _texts: list[str]

    def __init__(self, *, logger_factory: LoggerFactory) -> None:
        self._logger = logger_factory(__name__)

    def _load_pdf(self) -> None:
        docs = PyPDFLoader(FAQ_PDF).load()
        self._logger.info(
            "FAQ PDF loaded",
            details={"pages": len(docs)},
        )
        self._docs = docs

    def _split_document(self) -> None:
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=settings.faq_chunk_size,
            chunk_overlap=settings.faq_chunk_overlap,
        )
        chunks = splitter.split_documents(self._docs)
        self._logger.debug("Chunks generated", details={"amount": len(chunks)})
        self._chunks = chunks

    def _extract_texts(self) -> None:
        self._texts = [chunk.page_content for chunk in self._chunks]

    def _embed_batches(self, *, collection_name: str) -> None:
        for i in range(0, len(self._texts), settings.faq_ingestion_batch_size):
            batch_texts = self._texts[i : i + settings.faq_ingestion_batch_size]
            batch_chunks = self._chunks[i : i + settings.faq_ingestion_batch_size]

            self._logger.info(
                "Generating embeddings for chunks...",
                details={
                    "total": len(self._chunks),
                    "batch_size": settings.faq_ingestion_batch_size,
                    "iterator": i,
                },
            )
            vectors = qdrant_embeddings.generate_batch(batch_texts)

            if len(vectors) != len(batch_chunks):
                raise RuntimeError(
                    "Vectorization generated a different number of "
                    "vectors compared to the input chunks"
                )

            points = [
                models.PointStruct(
                    id=str(uuid.uuid4()),
                    vector=vector,
                    payload={
                        "page_content": chunk.page_content,
                        "page_number": chunk.metadata.get("page", 0),
                        "source": FAQ_PDF.name,
                    },
                )
                for vector, chunk in zip(vectors, batch_chunks)
            ]

            qdrant_client.upsert(
                collection_name=collection_name,
                points=points,
                wait=True,
            )

    def _create_versioned_collection(self) -> str:
        collection_name = f"{settings.faq_collection_prefix}-{uuid.uuid4()}"
        created = qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=models.VectorParams(
                size=settings.embedding_dimmensions,
                distance=models.Distance.COSINE,
            ),
        )
        if not created:
            raise RuntimeError("QDrant did not create the FAQ collection")
        return collection_name

    def _collection_size_matches_chunks_amount(self, *, collection_name: str) -> bool:
        result = qdrant_client.count(
            collection_name=collection_name,
        )
        return result.count == len(self._chunks)

    def _current_alias_target(self) -> str | None:
        aliases = qdrant_client.get_aliases().aliases
        return next(
            (
                alias.collection_name
                for alias in aliases
                if alias.alias_name == settings.faq_collection_alias
            ),
            None,
        )

    def _activate_collection(self, *, collection_name: str) -> str | None:
        previous_collection = self._current_alias_target()
        operations: list[models.CreateAliasOperation | models.DeleteAliasOperation] = []

        if previous_collection is not None:
            operations.append(
                models.DeleteAliasOperation(
                    delete_alias=models.DeleteAlias(
                        alias_name=settings.faq_collection_alias
                    )
                )
            )

        operations.append(
            models.CreateAliasOperation(
                create_alias=models.CreateAlias(
                    collection_name=collection_name,
                    alias_name=settings.faq_collection_alias,
                )
            )
        )

        updated = qdrant_client.update_collection_aliases(
            change_aliases_operations=operations
        )
        if not updated:
            raise RuntimeError("QDrant did not activate the new FAQ collection")

        if previous_collection is not None:
            try:
                deleted = qdrant_client.delete_collection(
                    collection_name=previous_collection
                )
                if not deleted:
                    self._logger.warning(
                        "Previous FAQ collection was not removed",
                        details={"collection": previous_collection},
                    )
            except Exception as error:
                self._logger.warning(
                    "Failed to remove previous FAQ collection",
                    details={
                        "collection": previous_collection,
                        "error_type": type(error).__name__,
                    },
                )
        return previous_collection

    def _make_ingestion(self) -> int:
        new_collection: str | None = None

        try:
            self._load_pdf()
            self._split_document()

            if self._chunks == []:
                raise RuntimeError("Document splitting generated no chunks")

            self._extract_texts()
            new_collection = self._create_versioned_collection()
            self._embed_batches(collection_name=new_collection)

            if not self._collection_size_matches_chunks_amount(
                collection_name=new_collection
            ):
                raise RuntimeError(
                    "FAQ collection point count differs from generated chunks"
                )

            previous_collection = self._activate_collection(
                collection_name=new_collection
            )
            self._logger.info(
                "FAQ collection activated",
                details={
                    "collection": new_collection,
                    "previous_collection": previous_collection,
                },
            )
        except Exception as error:
            if new_collection is not None:
                qdrant_client.delete_collection(collection_name=new_collection)
            self._logger.exception(
                "FAQ ingestion failed",
                exception=error,
            )
            raise

        return len(self._chunks)

    def ingest(self) -> tuple[bool, int]:
        """
        Ingest the FAQ PDF into QDrant database, if necessary.
        Returns (did insert, amount of chunks).
        """
        if not settings.ingest_faq_pdf:
            self._logger.info("Skipping FAQ PDF ingestion...")
            return False, 0

        self._logger.info("Ingesting PDF into vectorstore...")

        chunks = self._make_ingestion()

        self._logger.info(
            "Ingestion completed and indexed in QDrant",
            details={"amount": chunks},
        )

        return True, chunks
