from typing import Any, Awaitable, Callable, Sequence

from langchain.agents import create_agent
from langchain.agents.middleware import (
    AgentMiddleware,
    ModelRequest,
    ModelResponse,
)
from langchain_core.tools import BaseTool
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel

from app.infrastructure.settings import settings

SPECIALIST_TEMPERATURE: float = 0.7
SPECIALIST_TOP_P: float = 0.95


llm_gemini = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    temperature=SPECIALIST_TEMPERATURE,
    top_p=SPECIALIST_TOP_P,
    google_api_key=settings.gemini_api_key,
)

llm_groq = ChatGroq(
    model="qwen/qwen3.6-27b",
    temperature=SPECIALIST_TEMPERATURE,
    api_key=settings.groq_api_key,
    model_kwargs={"top_p": SPECIALIST_TOP_P},
)

fast_llm = ChatGroq(
    model="openai/gpt-oss-120b", temperature=0.0, api_key=settings.groq_api_key
)


def is_rate_limit_error(exc: Exception) -> bool:
    return getattr(exc, "status_code", None) == 429


class FallbackOn429Middleware(AgentMiddleware):
    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        try:
            return await handler(request)

        except Exception as e:
            if not is_rate_limit_error(e):
                raise

            fallback_request = request.override(model=llm_groq)

            return await handler(fallback_request)


def create_specialist(
    system_prompt: str,
    response_format: type[BaseModel],
    tools: Sequence[BaseTool | Callable[..., Any] | dict[str, Any]] | None = None,
) -> CompiledStateGraph:
    return create_agent(
        model=llm_gemini,
        system_prompt=system_prompt,
        response_format=response_format,
        tools=tools,
        middleware=[FallbackOn429Middleware()],
    )
