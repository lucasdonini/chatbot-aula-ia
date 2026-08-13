import logging
import re
from typing import Any, Optional

from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage
from langgraph.graph import END

from app.agents.llms import fast_llm
from app.agents.router import ROUTER_NODE_NAME
from app.infrastructure.execution_time_logger import log_execution_time
from app.model.graph_state import GraphState, GraphStateKeys
from app.model.guardrail_result import GuardrailResult

from .anonymization import anonymize_input
from .guardrails_config import BLOCK_RESPONSES, INJECTION_PATTERNS, INTERN_DATA_KEYWORDS
from .guardrails_prompts import CLASSIFIER_PROMPT

logger = logging.getLogger(__name__)


async def _input_guardrail(input: str) -> GuardrailResult:
    """Run input checks in ascendent cost order:
    Deterministic first, then LLM only if needed.
    """

    logger.debug(
        "Verifying input compliance",
        extra={"details": {"input_len": len(input)}},
    )

    # 1. Prompt injection
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, input, re.IGNORECASE):
            logger.debug(
                "Input blocked for prompt injection",
                extra={"details": {"reason": "prompt_injection", "input": input}},
            )
            return GuardrailResult.block(
                "prompt_injection", "Não consigo processar essa solicitação."
            )

    # 2. Tentativa de acesso a dados internos
    texto_lower = input.lower()
    for kw in INTERN_DATA_KEYWORDS:
        if kw in texto_lower:
            logger.debug(
                "Input blocked for PII",
                extra={"details": {"reason": "acesso_dados_internos"}},
            )
            return GuardrailResult.block(
                "acesso_dados_internos",
                "Não tenho como compartilhar informações internas do sistema.",
            )

    # 3. Classificação semântica via LLM
    try:
        response = (
            await fast_llm.ainvoke(CLASSIFIER_PROMPT.format(mensagem=input))
        ).content

        if not isinstance(response, str):
            raise TypeError(
                f"Classifier returned non-text content: {type(response).__name__!r}"
            )
    except Exception:
        logger.exception(
            "Input classifier failed",
            extra={"details": {"stage": "classification"}},
        )
        return GuardrailResult.block(
            "classificador_indisponivel",
            (
                "Não consigo processar essa solicitação no momento. "
                "Tente novamente mais tarde."
            ),
        )

    category: Optional[str] = None
    for line in response.splitlines():
        if line.strip().upper().startswith("CATEGORIA:"):
            category = line.split(":", 1)[1].strip().upper()
            break

    if category == "APROVADO":
        logger.debug(
            "Input approved",
            extra={"details": {"input": input, "category": category}},
        )
        return GuardrailResult.input_aproved(input)

    if category in BLOCK_RESPONSES:
        reason, message = BLOCK_RESPONSES[category]
        return GuardrailResult.block(reason, message)

    logger.warning(
        "Input blocked due to undetermined classification",
        extra={"details": {"category": category}},
    )
    return GuardrailResult.block(
        "classificacao_indeterminada",
        "Não consigo processar essa solicitação no momento. Tente reformulá-la.",
    )


INPUT_GUARDRAIL_NODE_NAME = "input_guardrail"


@log_execution_time
async def input_guardrail_node(state: GraphState) -> dict[GraphStateKeys, Any]:
    user_input = state["messages"][-1]
    assert user_input.id is not None

    anonymized, pii_map = anonymize_input(user_input.text)
    logger.info(
        "Agent called",
        extra={
            "details": {
                "name": INPUT_GUARDRAIL_NODE_NAME,
                "input_anonymized": anonymized,
            }
        },
    )
    result = await _input_guardrail(anonymized)

    if result.blocked:
        logger.info(
            "Agent response",
            extra={
                "details": {
                    "from": INPUT_GUARDRAIL_NODE_NAME,
                    "status": "blocked",
                    "reason": result.blocked,
                }
            },
        )
        return {
            GraphStateKeys.ROUTE: END,
            GraphStateKeys.CALLED_AGENTS: [INPUT_GUARDRAIL_NODE_NAME],
            GraphStateKeys.MESSAGES: [AIMessage(content=result.message)],
        }

    logger.info(
        "Agent response",
        extra={"details": {"from": INPUT_GUARDRAIL_NODE_NAME, "status": "approved"}},
    )
    return {
        GraphStateKeys.ROUTE: ROUTER_NODE_NAME,
        GraphStateKeys.CALLED_AGENTS: [INPUT_GUARDRAIL_NODE_NAME],
        GraphStateKeys.PII_MAP: pii_map,
        GraphStateKeys.MESSAGES: [
            RemoveMessage(id=user_input.id),
            HumanMessage(content=result.message),
        ],
    }
