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


@log_execution_time
def _output_guardrail(
    output: str, pii_map: dict, restaurar_pii: bool = False
) -> GuardrailResult:
    """
    Limpa e revisa a resposta do especialista antes de entregar ao usuário.
    Nunca bloqueia — sempre retorna o texto revisado em 'conteudo'.
    """

    logger.info("Verifying output compliance...")

    # 1. Remove PII que o modelo tenha gerado
    for type, pattern in PII:
        output = re.sub(pattern, f"[{type} OMITIDO]", output)

    # 2. Resolve tokens de PII da entrada
    output = deanonymize_output(output, pii_map, restore=restaurar_pii)

    # 3. Revisão de compliance financeiro
    result = fast_llm.invoke(COMPLIANCE_PROMPT.format(resposta=output)).content.strip()
    if "RESPOSTA:" in result:
        output = result.split("RESPOSTA:", 1)[1].strip() or output

    logger.debug("Output aproved: %s", output)
    return GuardrailResult.output_aproved(output)


OUTPUT_GUARDRAIL_NODE_NAME = "output_guardrail"


def output_guardrail_node(state: GraphState) -> dict[GraphStateKeys, Any]:
    logger.info("Output Guardrail called. State: %s", state)
    result = _output_guardrail(state["messages"][-1].text, state["pii_map"])
    return {
        GraphStateKeys.MESSAGES: [AIMessage(content=result.message)],
        GraphStateKeys.CALLED_AGENTS: [OUTPUT_GUARDRAIL_NODE_NAME],
    }
