from unittest.mock import AsyncMock, MagicMock

import pytest
from langchain_core.messages import AIMessage

from app.infrastructure.text_generator import LLMTextGenerator


@pytest.mark.asyncio
async def test_text_generator_returns_text_content() -> None:
    llm = MagicMock()
    llm.ainvoke = AsyncMock(return_value=AIMessage(content="resposta"))
    generator = LLMTextGenerator(llm)

    result = await generator.generate("prompt")

    assert result == "resposta"
    llm.ainvoke.assert_awaited_once_with("prompt")


@pytest.mark.asyncio
async def test_text_generator_rejects_non_text_content() -> None:
    llm = MagicMock()
    llm.ainvoke = AsyncMock(return_value=AIMessage(content=[{"type": "text"}]))
    generator = LLMTextGenerator(llm)

    with pytest.raises(TypeError, match="non-text content"):
        await generator.generate("prompt")
