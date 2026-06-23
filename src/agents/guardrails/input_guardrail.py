from typing import Any
import re

from langchain_core.messages import RemoveMessage

from src.model.common.graph_state import GraphState, GraphStateKeys
from src.model.common.guardrail_result import GuardrailResult
from src.utils import make_message_human, make_message_assistant
from .anonymization import anonymize_input
from ..llms import fast_llm

_INJECTION_PATTERNS = [
    r"ignore\s+(as\s+)?instru[çc][oõ]es",
    r"ignore\s+previous\s+instructions",
    r"forget\s+your\s+instructions",
    r"you\s+are\s+now\s+",
    r"act\s+as\s+(if\s+)?",
    r"pretend\s+(you\s+are|to\s+be)",
    r"jailbreak",
    r"dan\s+mode",
    r"modo\s+irrestrito",
    r"system\s*prompt",
    r"<\s*system\s*>",
    r"\[INST\]",
    r"###\s*instruction",
    r"override\s+(your\s+)?instructions",
    r"desconsider[ea]\s+(suas\s+)?instru[çc][oõ]es",
]

_INTERN_DATA_KEYWORDS = [
    "prompt do sistema",
    "system prompt",
    "suas instruções",
    "your instructions",
    "variável de ambiente",
    "chave de api",
    "api key",
    "senha do sistema",
    "token de acesso",
    "banco de dados interno",
    "tabela interna",
    "dados de outros clientes",
    "lista de clientes",
    "credenciais",
]

# Uma chamada LLM para as 5 categorias semânticas
_CLASSIFIER_PROMPT = """\
Você é um classificador de segurança de um sistema de assessoria financeira e agenda.
Classifique a mensagem em UMA categoria. Responda SOMENTE:

CATEGORIA: [categoria]
JUSTIFICATIVA: [uma linha]

Categorias:
APROVADO        - mensagem legítima sobre finanças (informativa), agenda ou operações
OFENSIVO        - xingamentos, assédio, discurso de ódio
PERIGOSO        - instruções que causam dano físico, psicológico ou coletivo
ILICITO         - pedido de auxílio para atividades ilegais ou fraudulentas
POLITICO        - opiniões ou debates políticos, partidos, eleições
INDICACAO_INVEST - recomendação direta de ativo específico para comprar/vender/manter

Mensagem: {mensagem}
"""

_BLOCK_RESPONSES = {
    "OFENSIVO": (
        "conteudo_ofensivo",
        "Por favor, mantenha um tom respeitoso para que eu possa te ajudar.",
    ),
    "PERIGOSO": ("pedido_perigoso", "Não posso ajudar com esse tipo de solicitação."),
    "ILICITO": (
        "pedido_ilicito",
        "Não posso auxiliar com atividades ilegais ou irregulares.",
    ),
    "POLITICO": (
        "pergunta_politica",
        "Não me envolvo em temas políticos. Posso ajudar com finanças ou sua agenda.",
    ),
    "INDICACAO_INVEST": (
        "indicacao_investimento",
        "Por regulação, não forneço indicações diretas de ativos. Posso explicar classes de investimento ou agendar uma reunião com seu assessor.",
    ),
}


def _input_guardrail(input: str) -> GuardrailResult:
    """Run input checks in ascendent cost order:
    Deterministic first, then LLM only if needed.
    """

    # 1. Prompt injection
    for pattern in _INJECTION_PATTERNS:
        if re.search(pattern, input, re.IGNORECASE):
            return GuardrailResult.block(
                "prompt_injection", "Não consigo processar essa solicitação."
            )

    # 2. Tentativa de acesso a dados internos
    texto_lower = input.lower()
    for kw in _INTERN_DATA_KEYWORDS:
        if kw in texto_lower:
            return GuardrailResult.block(
                "acesso_dados_internos",
                "Não tenho como compartilhar informações internas do sistema.",
            )

    # 3. Classificação semântica via LLM (ofensivo, perigoso, ilícito, político, indicação)
    resposta = fast_llm.invoke(_CLASSIFIER_PROMPT.format(mensagem=input)).content

    categoria = "APROVADO"
    for linha in resposta.splitlines():
        if linha.strip().upper().startswith("CATEGORIA:"):
            categoria = linha.split(":", 1)[1].strip().upper()
            break

    if categoria in _BLOCK_RESPONSES:
        motivo, mensagem = _BLOCK_RESPONSES[categoria]
        return GuardrailResult.block(motivo, mensagem)

    return GuardrailResult.input_aproved()


def input_guardrail_node(state: GraphState) -> dict[GraphStateKeys, Any]:
    user_input = state["messages"][-1]
    anonymized, pii_map = anonymize_input(user_input.text)
    result = _input_guardrail(anonymized)

    if result.blocked:
        return {
            GraphStateKeys.ROUTE: "fim",
            GraphStateKeys.CALLED_AGENTS: [f"guardrail_entrada -> {result.reason}"],
            GraphStateKeys.MESSAGES: [make_message_assistant(result.message)],
        }

    return {
        GraphStateKeys.ROUTE: "roteador",
        GraphStateKeys.CALLED_AGENTS: [f"guardrail_entrada -> {result.reason}"],
        GraphStateKeys.PII_MAP: pii_map,
        GraphStateKeys.MESSAGES: [
            RemoveMessage(id=user_input.id),
            make_message_human(result.message),
        ],
    }
