from langchain.tools import tool
from langchain_core.documents.base import Document
from langchain_core.tools import BaseTool
from pydantic import BaseModel, Field

from app.application.ports.logger import Logger
from app.infrastructure.faiss_store import get_faq_db


class GetFAQAnswerArgsSchema(BaseModel):
    question: str = Field(..., description="Pergunta do usuário a ser respondida")


TOOL_NAME = "faq_retreiver"


def create_faq_retriever(logger: Logger) -> BaseTool:
    @tool(TOOL_NAME, args_schema=GetFAQAnswerArgsSchema)
    def faq_retriever(question: str) -> list[Document]:
        """Busca no FAQ oficial os trechos relevantes para responder a pergunta."""
        logger.debug("Tool called", details={"tool": TOOL_NAME})
        db = get_faq_db()
        return db.similarity_search(question, k=6)

    return faq_retriever
