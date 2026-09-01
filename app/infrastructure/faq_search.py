from app.application.ports.faq_search import FaqSearch

from .faiss_store import get_faq_db


class FaissFaqSearch(FaqSearch):
    def search(self, question: str, *, limit: int) -> list[str]:
        documents = get_faq_db().similarity_search(question, k=limit)
        return [document.page_content for document in documents]
