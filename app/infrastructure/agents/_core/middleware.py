from typing import Awaitable, Callable

from langchain.agents.middleware import (
    AgentMiddleware,
    ModelRequest,
    ModelResponse,
)
from langchain.chat_models import BaseChatModel


def is_rate_limit_error(exc: Exception) -> bool:
    return getattr(exc, "status_code", None) == 429


class FallbackOn429Middleware(AgentMiddleware):
    def __init__(self, fallback_llm: BaseChatModel) -> None:
        self._fallback_llm = fallback_llm

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

            fallback_request = request.override(model=self._fallback_llm)

            return await handler(fallback_request)
