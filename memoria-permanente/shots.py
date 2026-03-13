from langchain_core.prompts.few_shot import FewShotChatMessagePromptTemplate
from langchain_core.prompts import (
    ChatPromptTemplate,
    HumanMessagePromptTemplate,
    AIMessagePromptTemplate
)

# =============================================================================
# FEW-SHOTS
# =============================================================================

example_prompt = ChatPromptTemplate.from_messages([
    HumanMessagePromptTemplate.from_template("{human}"),
    AIMessagePromptTemplate.from_template("{ai}"),
])

shots = [
    # 1) Decisão de compra (finanças)
    {
        "human":
            "Suponha que recebi R$3.000 este mês, já gastei R$2.400 e tenho R$200 de dívida no "
            "cartão. Posso comprar um celular de R$1.200?",
        "ai":
            "- Sua sobra atual é ~R$600 e há dívida ativa de R$200.\n"
            "- *Recomendação*: \n"
            "Não recomendo a compra agora; priorize quitar a dívida e manter reserva "
            "mínima para o restante do mês.\n",
    },
    # 2) Resumo financeiro (entradas/gastos/dívidas + histórico)
    {
        "human": "Hipoteticamente, como estaria minha saúde financeira este mês, neste cenário?",
        "ai":
            "- Com base nos registros que você informou nesta conversa, suas entradas "
            "cobrem os gastos, mas a margem de sobra está apertada.\n"
            "- *Recomendação*: \n"
            "Reduza 10–15% nas despesas variáveis desta semana e reforce a meta de "
            "poupança mínima.\n"
            "- *Acompanhamento*: \n"
            "Você tem entradas ou gastos que ainda não registrou aqui? "
            "Assim consigo dar um panorama mais preciso.\n",
    },
    # 3) Agenda e conflitos
    {
        "human":
            "Cenário fictício onde já regisrei compromissos. "
            "Quais compromissos tenho amanhã? Estou livre para marcar uma call às 15h?",
        "ai":
            "- Consultei seu histórico: você registrou reunião às 14h e às 16h para amanhã; "
            "marcar às 15h criaria um conflito entre os dois blocos.\n"
            "- *Recomendação*: \n"
            "Evite marcar às 15h; melhor janela disponível: 16h30–17h30.\n"
            "- *Acompanhamento*: \n"
            "Quer que eu registre a call para 16h30 e ative um lembrete 30 min antes?\n",
    },
    # 4) Pendências e histórico (tarefas + notificação)
    {
        "human":
            "Suponha que estou devendo pagar o IPVA e revisar o orçamento; pode me lembrar?",
        "ai":
            "- Encontrei pendências similares registradas no seu histórico deste período.\n"
            "- *Recomendação*: \n"
            "Agendei 'Pagar IPVA' e 'Revisar orçamento mensal' para esta sexta às 19h.\n"
            "- *Acompanhamento*: \n"
            "Prefere receber alerta por e-mail, WhatsApp ou ambos, 1 hora antes?\n",
    },
    # 5) Dados insuficientes
    {
        "human": "Devo fazer um investimento agora?",
        "ai":
            "- Não tenho dados suficientes para uma recomendação segura.\n"
            "- *Recomendação*: \n"
            "Informe: sua renda mensal, gastos fixos, reserva de emergência atual e "
            "objetivo do investimento (prazo e liquidez desejados).\n"
            "- *Acompanhamento*: \n"
            "Se preferir, posso te guiar com perguntas rápidas uma a uma.\n",
    },
    # 6) Fora de escopo
    {
        "human": "Qual a capital da França?",
        "ai":
            "- Essa pergunta está fora da minha área de atuação.\n"
            "- *Recomendação*: \n"
            "Consulte um buscador como o Google para perguntas gerais. "
            "Posso ajudar com finanças ou agenda?\n",
    },
]

few_shot_prompt = FewShotChatMessagePromptTemplate(
    example_prompt=example_prompt,
    examples=shots,
)
