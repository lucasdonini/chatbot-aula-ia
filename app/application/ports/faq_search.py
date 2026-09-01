from typing import Protocol, runtime_checkable


@runtime_checkable
class FaqSearch(Protocol):
    def search(self, question: str, *, limit: int) -> list[str]: ...
