from typing import TypedDict, Annotated
from enum import StrEnum
import operator


class GraphState(TypedDict):
    input: str  # sobrescrito a cada etapa
    session_id: str  # ID da sessão
    called_agents: Annotated[list[str], operator.add]  # acumula entre nós
    specialist_output: str  # JSON do especialista ativo
    final_output: str  # resposta para o usuário


class GraphStateKeys(StrEnum):
    INPUT = "input"
    SESSION_ID = "session_id"
    CALLED_AGENTS = "called_agents"
    SPECIALIST_OUTPUT = "specialist_output"
    FINAL_OUTPUT = "final_output"
