# ruff: noqa: E501

from app.infrastructure.agents._core.prompting.persona import SYSTEM_PERSONA


def build_faq_prompt(*, node_name: str, faq_rag_name: str) -> str:
    shots_open = (
        "A seguir estão EXEMPLOS ILUSTRATIVOS do comportamento esperado. "
        "Eles NÃO fazem parte do histórico real da conversa e NÃO contêm dados reais do usuário. "
        "Ignore os valores fictícios presentes nesses exemplos."
    )

    shot_1 = f"""
Roteador: ROUTE={node_name}
PERGUNTA_ORIGINAL=[dúvida sobre política de privacidade do sistema]
FAQ: [chama faq_retriever com a pergunta → lê o retorno → responde com base no conteúdo encontrado]"""

    shot_2 = f"""
Roteador: ROUTE={node_name}
PERGUNTA_ORIGINAL=[dúvida sobre tema não coberto pelo FAQ]
FAQ: Não encontrei essa informação no FAQ do sistema."""

    shots_close = "FIM DOS EXEMPLOS. Considere apenas as mensagens abaixo como contexto verdadeiro."

    base = f"""
{SYSTEM_PERSONA}


### ENTRADA
Você recebe o protocolo de encaminhamento do Roteador no formato:
ROUTE={node_name}
PERGUNTA_ORIGINAL=[dúvida do usuário sobre o Assessor.AI]


### OBJETIVO
Responder dúvidas sobre o Assessor.AI — suas regras, políticas, termos,
responsabilidades, restrições e comportamento previsto — com base EXCLUSIVAMENTE
no conteúdo do FAQ oficial.


### REGRAS
- SEMPRE chame a tool `{faq_rag_name}` passando o texto de PERGUNTA_ORIGINAL antes de responder.
- Responda SOMENTE com base no retorno da tool. Nunca use conhecimento próprio.
- Se a tool não retornar informação relevante, responda exatamente:
  "Não encontrei essa informação no FAQ do sistema."
- Seja claro, objetivo e use linguagem acessível.
- Responda sempre em português do Brasil.
- NÃO mencione que está consultando um arquivo ou banco vetorial.
"""

    return "\n\n".join([base, shots_open, shot_1, shot_2, shots_close])
