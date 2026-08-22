from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq

from app.infrastructure.settings import settings

SPECIALIST_TEMPERATURE: float = 0.7
SPECIALIST_TOP_P: float = 0.95


llm_gemini = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=SPECIALIST_TEMPERATURE,
    top_p=SPECIALIST_TOP_P,
    google_api_key=settings.gemini_api_key,
    timeout=settings.llm_request_timeout_seconds,
)

llm_groq = ChatGroq(
    model="qwen/qwen3.6-27b",
    temperature=SPECIALIST_TEMPERATURE,
    api_key=settings.groq_api_key,
    model_kwargs={"top_p": SPECIALIST_TOP_P},
    timeout=settings.llm_request_timeout_seconds,
)

fast_llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.0,
    api_key=settings.groq_api_key,
    timeout=settings.llm_request_timeout_seconds,
)
