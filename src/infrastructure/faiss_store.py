import logging

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

from src.infrastructure.execution_time_logger import log_execution_time

from .paths import FAQ_INDEX, FAQ_PDF
from .settings import settings

logger = logging.getLogger(__name__)


def _get_embeddings() -> GoogleGenerativeAIEmbeddings:
    return GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-2-preview", api_key=settings.gemini_api_key
    )


def _build_db() -> FAISS:
    docs = PyPDFLoader(FAQ_PDF).load()
    logger.info(
        "FAQ PDF loaded",
        extra={"details": {"pages": len(docs)}},
    )

    splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=150)
    chunks = splitter.split_documents(docs)
    embeddings = _get_embeddings()
    db = FAISS.from_documents(chunks, embeddings)
    logger.info("FAQ index built")

    db.save_local(str(FAQ_INDEX))
    logger.info("FAQ index saved locally")

    return db


@log_execution_time
def get_faq_db() -> FAISS:
    pdf_mtime = FAQ_PDF.stat().st_mtime
    mtime_file = FAQ_INDEX / "mtime.txt"

    if not FAQ_INDEX.exists() or not mtime_file.exists():
        logger.info("FAQ index not cached, building new")
        db = _build_db()
        mtime_file.write_text(str(pdf_mtime))
        return db

    cached_mtime = float(mtime_file.read_text())
    if pdf_mtime != cached_mtime:
        logger.info("FAQ PDF modified, rebuilding index")
        db = _build_db()
        mtime_file.write_text(str(pdf_mtime))
        return db

    logger.debug("Using cached FAQ index")
    return FAISS.load_local(
        str(FAQ_INDEX), _get_embeddings(), allow_dangerous_deserialization=True
    )
