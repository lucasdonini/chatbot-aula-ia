from .agents import router_app, orquestrator_app, SPECIALISTS, CONSULTANTS
from .infrastructure.md_console import print

import os
import re


def invoke_agent(agent, user_input: str, session_id: str) -> str:
    response = agent.invoke(
        {"messages": [{"role": "human", "content": user_input}]},
        config={"configurable": {"thread_id": session_id}},
    )
    return response["messages"][-1].text


def make_question(user_input: str, session_id: str) -> str:
    try:
        router_response = invoke_agent(router_app, user_input, session_id)

        match = re.search(r"(?<=ROUTE=)\w+", router_response)
        if not match:
            return router_response
        agent_name = match.group()

        if specialist := SPECIALISTS.get(agent_name):
            specialist_response = invoke_agent(specialist, router_response, session_id)
            return invoke_agent(orquestrator_app, specialist_response, session_id)

        if consultant := CONSULTANTS.get(agent_name):
            return invoke_agent(consultant, router_response, session_id)

        return f"Erro no roteador: agente {agent_name} não encontrado"

    except Exception as e:
        return f"Erro no roteador: {e}"


os.system("cls")
print("\n# Bem vindo! Converse hoje mesmo com o Assessor.IA!!\n")

while True:
    user_input = input(">>> ")
    if user_input.lower() in ("sair", "exit", "tchau", "bye", "end", "fim"):
        print("Encerrando a conversa")
        break

    response = make_question(user_input, "meu_id_de_sessao")
    print(f"\n{response}\n---\n\n")
