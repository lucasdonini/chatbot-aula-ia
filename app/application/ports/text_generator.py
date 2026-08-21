from typing import Protocol


class TextGenerator(Protocol):
    async def generate(self, prompt: str) -> str: ...
