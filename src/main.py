from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_groq import ChatGroq
from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver

from datetime import datetime
import os

from .agents import router_app, financial_app, agenda_app, orquestrator_app


os.system("cls")
print("\nBem vindo! Converse hoje mesmo com o Acessor.IA!!", "\n")

while True:
    user_input = input(">>> ")
    if user_input.lower() in ("sair", "exit", "tchau", "bye", "end", "fim"):
        print("Encerrando a conversa")
        break
    try:
        resposta = router_app.invoke(
            {
                "messages": [
                    {"role": "human", "content": f"{datetime.now()} -> {user_input}"}
                ]
            },
            config={"configurable": {"thread_id": "meu_id_de_sessao"}},
        )
        print(f"\n{resposta['messages'][-1].text}\n{'-' * 20}\n")
    except Exception as e:
        print("Erro ao consumir API:", e)
        break
