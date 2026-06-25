import logging
from typing import List

from langchain.tools import tool
from langchain_core.documents.base import Document
from pydantic import BaseModel, Field

from src.infrastructure.faiss_store import get_faq_db

logger = logging.getLogger(__name__)


class GetFAQAnswerArgsSchema(BaseModel):
    question: str = Field(..., description="Pergunta do usuário a ser respondida")


@tool(args_schema=GetFAQAnswerArgsSchema)
def faq_retriever(question: str) -> List[Document]:
    """Busca no FAQ oficial os trechos mais relevantes para responder a pergunta."""
    logger.info("faq_retriever tool called")
    db = get_faq_db()
    return db.similarity_search(question, k=6)
