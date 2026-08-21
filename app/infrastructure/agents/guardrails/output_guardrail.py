import logging
import re
from typing import Any, ClassVar

from langchain_core.messages import AIMessage

from app.application.ports.text_generator import TextGenerator
from app.infrastructure.agents._core.contracts.agent_node import AgentNode
from app.infrastructure.agents._core.state import GraphState, GraphStateKeys
from app.infrastructure.agents.guardrails.result import GuardrailResult
from app.infrastructure.execution_time_logger import log_execution_time

from .anonymization import deanonymize_output
from .anonymization_config import PII
from .guardrails_prompts import COMPLIANCE_PROMPT

logger = logging.getLogger(__name__)


class OutputGuardrailNode(AgentNode):
    name: ClassVar[str] = "output_guardrail"

    def __init__(self, text_generator: TextGenerator) -> None:
        self._text_generator = text_generator

    async def _guard_output(
        self,
        output: str,
        pii_map: dict,
        restore_pii: bool = False,
    ) -> GuardrailResult:
        logger.debug(
            "Verifying output compliance",
            extra={"details": {"output_len": len(output)}},
        )

        for pii_type, pattern in PII:
            output = re.sub(pattern, f"[{pii_type} OMITIDO]", output)

        output = deanonymize_output(output, pii_map, restore=restore_pii)
        result = await self._text_generator.generate(
            COMPLIANCE_PROMPT.format(resposta=output)
        )
        result = result.strip()

        if "RESPOSTA:" in result:
            output = result.split("RESPOSTA:", 1)[1].strip() or output

        logger.debug(
            "Output approved",
            extra={"details": {"output": output[:200]}},
        )
        return GuardrailResult.output_aproved(output)

    @log_execution_time
    async def __call__(self, state: GraphState) -> dict[GraphStateKeys, Any]:
        logger.info(
            "Agent called",
            extra={"details": {"name": self.name, "input": "(sanitized)"}},
        )
        result = await self._guard_output(
            state["messages"][-1].text,
            state["pii_map"],
        )
        logger.info(
            "Agent response",
            extra={
                "details": {
                    "from": self.name,
                    "output": result.message[:500],
                }
            },
        )
        return {
            GraphStateKeys.MESSAGES: [AIMessage(content=result.message)],
            GraphStateKeys.CALLED_AGENTS: [self.name],
        }
