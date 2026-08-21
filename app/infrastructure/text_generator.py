from langchain.chat_models import BaseChatModel


class LLMTextGenerator:
    def __init__(self, llm: BaseChatModel) -> None:
        self._llm = llm

    async def generate(self, prompt: str) -> str:
        result = await self._llm.ainvoke(prompt)
        if not isinstance(result.content, str):
            raise TypeError(
                "Text generator returned non-text content: "
                f"{type(result.content).__name__!r}"
            )
        return result.content
