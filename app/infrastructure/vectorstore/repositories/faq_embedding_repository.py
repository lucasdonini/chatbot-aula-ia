from app.application.ports.faq_search import FaqSearch
from app.application.ports.logger import LoggerFactory
from app.infrastructure.settings import settings

from ..client import qdrant_client
from ..embeddings import qdrant_embeddings


class QDrantFaqSearch(FaqSearch):
    def __init__(self, *, logger_factory: LoggerFactory) -> None:
        self._logger = logger_factory(__name__)

    def search(self, question: str, *, limit: int) -> list[str]:
        self._logger.debug("Searching FAQ", details={"limit": limit})

        vector = qdrant_embeddings.generate(question)
        query_results = qdrant_client.query_points(
            collection_name=settings.faq_collection_alias,
            query=vector,
            limit=limit,
            score_threshold=settings.faq_search_score_threshold,
            with_payload=["page_content"],
        )

        results = []
        scores = []
        for point in query_results.points:
            content = None
            if payload := point.payload:
                content = payload.get("page_content", None)
            if not isinstance(content, str):
                self._logger.warning(
                    "FAQ search found non processable content",
                    details={
                        "expected_type": str.__name__,
                        "received_type": type(content).__name__,
                    },
                )
                continue
            scores.append(point.score)
            results.append(content)

        scores = [round(s, 2) for s in scores]
        self._logger.debug(
            "FAQ search completed",
            details={
                "result_size": len(results),
                "result_scores": scores,
            },
        )
        return results
