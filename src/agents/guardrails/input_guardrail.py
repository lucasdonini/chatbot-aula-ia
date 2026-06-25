import logging
import re
import time
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage
from langgraph.graph import END

from src.model.graph_state import GraphState, GraphStateKeys
from src.model.guardrail_result import GuardrailResult

from ..llms import fast_llm
from ..router import ROUTER_NODE_NAME
from .anonymization import anonymize_input
from .guardrails_config import BLOCK_RESPONSES, INJECTION_PATTERNS, INTERN_DATA_KEYWORDS
from .guardrails_prompts import CLASSIFIER_PROMPT

logger = logging.getLogger(__name__)


def _input_guardrail(input: str) -> GuardrailResult:
    """Run input checks in ascendent cost order:
    Deterministic first, then LLM only if needed.
    """

    logger.info("Verifying input compliance...")

    # 1. Prompt injection
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, input, re.IGNORECASE):
            logger.debug("Input blocked for prompt injection: %s", input)
            return GuardrailResult.block(
                "prompt_injection", "Não consigo processar essa solicitação."
            )

    # 2. Tentativa de acesso a dados internos
    texto_lower = input.lower()
    for kw in INTERN_DATA_KEYWORDS:
        if kw in texto_lower:
            logger.debug("Input blocked for PII.")
            return GuardrailResult.block(
                "acesso_dados_internos",
                "Não tenho como compartilhar informações internas do sistema.",
            )

    # 3. Classificação semântica via LLM
    resposta = fast_llm.invoke(CLASSIFIER_PROMPT.format(mensagem=input)).content

    categoria = "APROVADO"
    for linha in resposta.splitlines():
        if linha.strip().upper().startswith("CATEGORIA:"):
            categoria = linha.split(":", 1)[1].strip().upper()
            break

    if categoria in BLOCK_RESPONSES:
        motivo, mensagem = BLOCK_RESPONSES[categoria]
        return GuardrailResult.block(motivo, mensagem)

    logger.debug("Input aproved: %s", input)
    return GuardrailResult.input_aproved(input)


INPUT_GUARDRAIL_NODE_NAME = "input_guardrail"


def input_guardrail_node(state: GraphState) -> dict[GraphStateKeys, Any]:
    start_time = time.perf_counter()
    logger.info("Input Guardrail called. State: %s", state)
    user_input = state["messages"][-1]
    anonymized, pii_map = anonymize_input(user_input.text)
    result = _input_guardrail(anonymized)

    end_time = time.perf_counter()
    logger.info("Input Guardrail node finished. Time: %s", end_time - start_time)

    if result.blocked:
        return {
            GraphStateKeys.ROUTE: END,
            GraphStateKeys.CALLED_AGENTS: [INPUT_GUARDRAIL_NODE_NAME],
            GraphStateKeys.MESSAGES: [AIMessage(content=result.message)],
        }

    return {
        GraphStateKeys.ROUTE: ROUTER_NODE_NAME,
        GraphStateKeys.CALLED_AGENTS: [INPUT_GUARDRAIL_NODE_NAME],
        GraphStateKeys.PII_MAP: pii_map,
        GraphStateKeys.MESSAGES: [
            RemoveMessage(id=user_input.id),
            HumanMessage(content=result.message),
        ],
    }
