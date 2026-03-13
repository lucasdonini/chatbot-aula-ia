from dotenv import load_dotenv
import os

from chain import chain


def main():
    print("\nBem vindo! Converse com seu acessor pessoal e organize sua vida!!\n")
    while True:
        user_input = input(">>> ")
        if user_input.lower() in ('sair', 'exit', 'tchau', 'bye', 'end', 'fim'):
            print('Encerrando a conversa')
            break
        try:
            resposta = chain.invoke(
                {"usuario": user_input},
                config={"configurable": {"session_id": "0"}}
            )
            print(f"\n{resposta}\n{'-' * 20}\n")
        except Exception as e:
            err_msg = str(e)
            
            if "429" in err_msg:
                msg = "Limite de requisições atingido. Tente novamente mais tarde"
            else:
                msg = f"Erro ao consumir API: {e}"
            
            print(msg)
            break


if __name__ == '__main__':
    os.system("cls")
    load_dotenv()
    main()
