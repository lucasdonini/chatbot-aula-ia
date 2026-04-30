from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_core.documents.base import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain.tools import tool
from pydantic import BaseModel, Field
from pathlib import Path
from typing import List

from src.model.env import env

PDF_PATH = Path(__file__).parent / "FAQ_assessor_v1.1.pdf"

docs = PyPDFLoader(PDF_PATH).load()
splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=150)
chunks = splitter.split_documents(docs)
embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-2-preview", api_key=env.gemini_api_key
)
db = FAISS.from_documents(chunks, embeddings)


class GetFAQAnswerArgsSchema(BaseModel):
    question: str = Field(..., description="Pergunta do usuário a ser respondida")


@tool(args_schema=GetFAQAnswerArgsSchema)
def faq_retreiver(question: str) -> List[Document]:
    """Busca no FAQ oficial os trechos mais relevantes para responder a pergunta."""
    return db.similarity_search(question, k=6)
