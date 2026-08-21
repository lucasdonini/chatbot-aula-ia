from collections.abc import Sequence

from langchain.agents import create_agent
from langchain.agents.middleware import AgentMiddleware
from langchain.chat_models import BaseChatModel
from langchain.tools import BaseTool
from langgraph.graph.state import CompiledStateGraph
from pydantic import BaseModel


class LangChainAgentFactory:
    def __init__(
        self,
        *,
        llm: BaseChatModel,
        tools: Sequence[BaseTool] = (),
        middlewares: Sequence[AgentMiddleware] = (),
    ) -> None:
        self._llm = llm
        self._tools = tuple(tools)
        self._middlewares = tuple(middlewares)

    def create(
        self,
        *,
        system_prompt: str,
        response_format: type[BaseModel] | None = None,
    ) -> CompiledStateGraph:
        return create_agent(
            model=self._llm,
            system_prompt=system_prompt,
            response_format=response_format,
            tools=list(self._tools),
            middleware=list(self._middlewares),
        )
