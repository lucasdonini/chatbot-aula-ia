from .infrastructure.md_console import print
from .infrastructure.logger import setup_logger
from .agents import execute_agent_flux

import logging
import os

setup_logger()
logger = logging.getLogger(__name__)


logger.info("App started")
os.system("cls")
print("\n# Bem vindo! Converse hoje mesmo com o Assessor.IA!!\n")

while True:
    user_input = input(">>> ")
    if user_input.lower() in ("sair", "exit", "tchau", "bye", "end", "fim"):
        print("Encerrando a conversa")
        break

    response = execute_agent_flux(user_input, "meu_id_de_sessao")
    print(f"\n{response}\n\n---\n\n")

logger.info("App closed")
