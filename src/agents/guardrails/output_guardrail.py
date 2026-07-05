import logging
import re
from typing import Any

from langchain_core.messages import AIMessage

from src.infrastructure.execution_time_logger import log_execution_time
from src.model.graph_state import GraphState, GraphStateKeys
from src.model.guardrail_result import GuardrailResult

from ..llms import fast_llm
from .anonymization import deanonymize_output
from .anonymization_config import PII
from .guardrails_prompts import COMPLIANCE_PROMPT

logger = logging.getLogger(__name__)


async def _output_guardrail(
    output: str, pii_map: dict, restaurar_pii: bool = False
) -> GuardrailResult:
    """
    Limpa e revisa a resposta do especialista antes de entregar ao usuário.
    Nunca bloqueia — sempre retorna o texto revisado em 'conteudo'.
    """

    logger.debug("Verifying output compliance...")

    # 1. Remove PII que o modelo tenha gerado
    for pii_type, pattern in PII:
        output = re.sub(pattern, f"[{pii_type} OMITIDO]", output)

    # 2. Resolve tokens de PII da entrada
    output = deanonymize_output(output, pii_map, restore=restaurar_pii)

    # 3. Revisão de compliance financeiro
    result = (await fast_llm.ainvoke(COMPLIANCE_PROMPT.format(resposta=output))).content

    if not isinstance(result, str):
        raise TypeError(
            f"Guardrail returned non-text content: {type(result).__name__!r}"
        )
    result = result.strip()

    if "RESPOSTA:" in result:
        output = result.split("RESPOSTA:", 1)[1].strip() or output

    logger.debug("Output aproved: %s", output)
    return GuardrailResult.output_aproved(output)


OUTPUT_GUARDRAIL_NODE_NAME = "output_guardrail"


@log_execution_time
async def output_guardrail_node(state: GraphState) -> dict[GraphStateKeys, Any]:
    logger.info("─" * 50)
    logger.info(" [NODE] OUTPUT GUARDRAIL ")
    result = await _output_guardrail(state["messages"][-1].text, state["pii_map"])
    logger.info(" Input: (sanitized)")
    logger.info(" Output: %s", result.message[:500])
    logger.info("─" * 50)
    return {
        GraphStateKeys.MESSAGES: [AIMessage(content=result.message)],
        GraphStateKeys.CALLED_AGENTS: [OUTPUT_GUARDRAIL_NODE_NAME],
    }
