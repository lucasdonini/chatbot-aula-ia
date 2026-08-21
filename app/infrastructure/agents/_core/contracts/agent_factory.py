from typing import Protocol

from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel


class AgentFactory(Protocol):
    def create(
        self,
        *,
        system_prompt: str,
        response_format: type[BaseModel] | None = None,
    ) -> CompiledStateGraph: ...
