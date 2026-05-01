from .agents import router_app, orquestrator_app, SPECIALISTS, CONSULTANTS
from .infrastructure.md_console import print
from .infrastructure.logger import setup_logger

import logging
import os
import re

setup_logger()
logger = logging.getLogger(__name__)


def invoke_agent(agent, user_input: str, session_id: str) -> str:
    response = agent.invoke(
        {"messages": [{"role": "human", "content": user_input}]},
        config={"configurable": {"thread_id": session_id}},
    )
    return response["messages"][-1].text


def make_question(user_input: str, session_id: str) -> str:
    try:
        logger.info("Agent invoked: router")
        router_response = invoke_agent(router_app, user_input, session_id)
        logger.debug("Router response: %s", router_response)

        match = re.search(r"(?<=ROUTE=)\w+", router_response)
        if not match:
            return router_response
        agent_name = match.group()
        logger.debug("Matched agent: %s from input: %s", agent_name, router_response)

        if specialist := SPECIALISTS.get(agent_name):
            logger.info(
                "Specialist invoked: %s -> input = %s", agent_name, router_response
            )
            specialist_response = invoke_agent(specialist, router_response, session_id)
            logger.debug("Specialist response: %s", specialist_response)

            logger.info(
                "Agent invoked: orquestrator -> input = %s", specialist_response
            )
            response = invoke_agent(orquestrator_app, specialist_response, session_id)
            logger.debug("Orquestrator response: %s", response)
            return response

        if consultant := CONSULTANTS.get(agent_name):
            logger.info(
                "Consultant invoked: %s -> input = %s", agent_name, router_response
            )
            response = invoke_agent(consultant, router_response, session_id)
            logger.debug("Consultant response: %s", response)
            return response

        logger.error("Router agent tried to access an unexisting agent: %s", agent_name)
        return f"Erro no roteador: agente {agent_name} não encontrado"

    except Exception as e:
        logger.exception("Exception raised while invoking agent")
        return f"Sinto muito, tivemos um erro interno. Tente novamente mais tarde."


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
