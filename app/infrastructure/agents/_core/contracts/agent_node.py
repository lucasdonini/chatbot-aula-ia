from abc import ABC, abstractmethod
from typing import Any, ClassVar

from ..state import GraphState, GraphStateKeys


class AgentNode(ABC):
    name: ClassVar[str]

    @abstractmethod
    async def __call__(self, state: GraphState) -> dict[GraphStateKeys, Any]: ...
