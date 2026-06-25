# ruff: noqa: E501

import logging
import re
import time
from typing import Any

from langchain_core.messages import AIMessage

from src.model.graph_state import GraphState, GraphStateKeys
from src.model.guardrail_result import GuardrailResult

from ..llms import fast_llm
from .anonymization import PII, deanonymize_output

logger = logging.getLogger(__name__)

_COMPLIANCE_PROMPT = """\
Você é um revisor de compliance para assessoria financeira regulada pela CVM e ANBIMA.
Corrija a resposta SOMENTE se ela garantir rentabilidade futura, recomendar ativo específico
sem disclaimer de risco, ou afirmar certeza sobre comportamento futuro do mercado.
Se estiver adequada, repita-a sem alterações.

Responda SOMENTE:
STATUS: APROVADO ou CORRIGIDO
RESPOSTA:
[texto final]

Resposta para revisar:
{resposta}
"""


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
    result = fast_llm.invoke(_COMPLIANCE_PROMPT.format(resposta=output)).content.strip()
    if "RESPOSTA:" in result:
        output = result.split("RESPOSTA:", 1)[1].strip() or output

    logger.debug("Output aproved: %s", output)
    return GuardrailResult.output_aproved(output)


OUTPUT_GUARDRAIL_NODE_NAME = "output_guardrail"


def output_guardrail_node(state: GraphState) -> dict[GraphStateKeys, Any]:
    start_time = time.perf_counter()
    logger.info("Output Guardrail called. State: %s", state)
    result = _output_guardrail(state["messages"][-1].text, state["pii_map"])
    end_time = time.perf_counter()
    logger.info("Output Guardrail node finished. Time: %s", end_time - start_time)
    return {
        GraphStateKeys.MESSAGES: [AIMessage(content=result.message)],
        GraphStateKeys.CALLED_AGENTS: [OUTPUT_GUARDRAIL_NODE_NAME],
    }
