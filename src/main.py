from .model.common.graph_state import GraphState
from .infrastructure.md_console import print
from .infrastructure.logger import setup_logger
from .agents import execute_agent_flux

import logging
import os

setup_logger()
logger = logging.getLogger(__name__)


def make_question(user_question: str, session_id: str) -> str:
    logger.info("Question made by user: %s", user_question)
    initial_state: GraphState = {
        "input": user_question,
        "session_id": session_id,
        "called_agents": [],
        "specialist_output": "",
        "final_output": "",
    }

    final_state = execute_agent_flux(initial_state, session_id)
    logger.info("Question anwered. Final state: %s", final_state)
    return final_state["final_output"]


logger.info("App started")
os.system("cls")
print("\n# Bem vindo! Converse hoje mesmo com o Assessor.IA!!\n")

while True:
    user_input = input(">>> ")
    if user_input.lower() in ("sair", "exit", "tchau", "bye", "end", "fim"):
        print("Encerrando a conversa")
        break

    response = make_question(user_input, "meu_id_de_sessao")
    print(f"\n{response}\n\n---\n\n")

logger.info("App closed")
