from .agents import router_app, orquestrator_app, SPECIALISTS
import os, re


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

        specialist_name = match.group()
        if not specialist_name in SPECIALISTS:
            return f"Erro no roteador: agente {specialist_name} não encontrado"

        specialist = SPECIALISTS[specialist_name]
        specialist_response = invoke_agent(specialist, router_response, session_id)

        return (
            invoke_agent(orquestrator_app, specialist_response, session_id)
            if specialist_name != "faq"
            else specialist_response
        )

    except Exception as e:
        print(f"Erro no roteador: {e}")


os.system("cls")
print("\nBem vindo! Converse hoje mesmo com o Assessor.IA!!", "\n")

while True:
    user_input = input(">>> ")
    if user_input.lower() in ("sair", "exit", "tchau", "bye", "end", "fim"):
        print("Encerrando a conversa")
        break

    response = make_question(user_input, "meu_id_de_sessao")
    print(f"\n{response}\n{'-' * 20}\n")
