import logging

from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_google_genai import GoogleGenerativeAIEmbeddings

from .settings import settings
from .paths import FAQ_INDEX, FAQ_PDF

logger = logging.getLogger(__name__)


def _get_embeddings() -> GoogleGenerativeAIEmbeddings:
    return GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-2-preview", api_key=settings.gemini_api_key
    )


def _build_db() -> FAISS:
    docs = PyPDFLoader(FAQ_PDF).load()
    logger.info("Loaded FAQ pdf")

    splitter = RecursiveCharacterTextSplitter(chunk_size=700, chunk_overlap=150)
    chunks = splitter.split_documents(docs)
    embeddings = _get_embeddings()
    db = FAISS.from_documents(chunks, embeddings)
    logger.info("Generated FAQ db")

    db.save_local(str(FAQ_INDEX))
    logger.info("FAQ db saved locally")

    return db


def get_faq_db() -> FAISS:
    pdf_mtime = FAQ_PDF.stat().st_mtime
    mtime_file = FAQ_INDEX / "mtime.txt"

    if not FAQ_INDEX.exists() or not mtime_file.exists():
        logger.info("Cached FAQ index not found. Using new db")
        db = _build_db()
        mtime_file.write_text(str(pdf_mtime))
        return db

    cached_mtime = float(mtime_file.read_text())
    if pdf_mtime != cached_mtime:
        logger.info("FAQ pdf was modified. Using new db")
        db = _build_db()
        mtime_file.write_text(str(pdf_mtime))
        return db

    logger.info("Using cached FAQ index")
    return FAISS.load_local(
        str(FAQ_INDEX), _get_embeddings(), allow_dangerous_deserialization=True
    )
