from typing import Annotated, Literal

from langchain.tools import BaseTool
from pydantic import BaseModel, Field

from app.application.ports.faq_search import FaqSearch
from app.application.ports.logger import LoggerFactory


class GetFAQAnswerArgsSchema(BaseModel):
    question: str = Field(..., description="Pergunta do usuário a ser respondida")


class FaqRag(BaseTool):
    name: Literal["faq_rag"] = "faq_rag"
    args_schema: type[BaseModel] = GetFAQAnswerArgsSchema
    description: str = (
        "Busca no FAQ oficial os trechos relevantes para responder a pergunta."
    )

    faq_search: Annotated[FaqSearch, Field(exclude=True)]
    logger_factory: Annotated[LoggerFactory, Field(exclude=True)]

    def _run(self, question: str) -> list[str]:
        logger = self.logger_factory(__name__)
        logger.debug("Tool called", details={"tool": self.name})
        return self.faq_search.search(question, limit=6)
