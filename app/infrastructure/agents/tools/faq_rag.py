from typing import Annotated, Literal

from langchain.tools import BaseTool
from langchain_core.documents.base import Document
from pydantic import BaseModel, Field

from app.application.ports.logger import LoggerFactory
from app.infrastructure.faiss_store import get_faq_db


class GetFAQAnswerArgsSchema(BaseModel):
    question: str = Field(..., description="Pergunta do usuário a ser respondida")


class FaqRag(BaseTool):
    name: Literal["faq_rag"] = "faq_rag"
    args_schema: type[BaseModel] = GetFAQAnswerArgsSchema
    description: str = (
        "Busca no FAQ oficial os trechos relevantes para responder a pergunta."
    )

    logger_factory: Annotated[LoggerFactory, Field(exclude=True)]

    def _run(self, question: str) -> list[Document]:
        logger = self.logger_factory(__name__)
        logger.debug("Tool called", details={"tool": self.name})
        db = get_faq_db()
        return db.similarity_search(question, k=6)
