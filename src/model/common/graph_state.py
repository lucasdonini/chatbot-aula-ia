from langgraph.graph import MessagesState
from typing import Annotated
from enum import StrEnum
import operator


class GraphState(MessagesState):
    called_agents: Annotated[list[str], operator.add]
    route: str
    pii_map: dict


class GraphStateKeys(StrEnum):
    MESSAGES = "messages"
    CALLED_AGENTS = "called_agents"
    ROUTE = "route"
    PII_MAP = "pii_map"
