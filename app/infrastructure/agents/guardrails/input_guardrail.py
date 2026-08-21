import logging
import re
from typing import Any, ClassVar, Final

from langchain_core.messages import AIMessage, HumanMessage, RemoveMessage
from langgraph.graph import END

from app.application.ports.text_generator import TextGenerator
from app.infrastructure.agents._core.state import GraphState, GraphStateKeys
from app.infrastructure.agents.guardrails.result import GuardrailResult
from app.infrastructure.execution_time_logger import log_execution_time

from .._core.contracts.agent_node import AgentNode
from .anonymization import anonymize_input
from .guardrails_config import BLOCK_RESPONSES, INJECTION_PATTERNS, INTERN_DATA_KEYWORDS
from .guardrails_prompts import CLASSIFIER_PROMPT

logger = logging.getLogger(__name__)


class InputGuardrailNode(AgentNode):
    name: ClassVar[str] = "input_guardrail"
    _text_generator: Final[TextGenerator]

    def __init__(self, *, text_generator: TextGenerator, approved_route: str) -> None:
        self._text_generator = text_generator
        self._approved_route = approved_route

    def _check_prompt_injection(self, input: str) -> bool:
        for pattern in INJECTION_PATTERNS:
            if re.search(pattern, input, re.IGNORECASE):
                logger.debug(
                    "Input blocked for prompt injection",
                    extra={"details": {"reason": "prompt_injection", "input": input}},
                )
                return False
        return True

    def _check_pii_access(self, input: str) -> bool:
        text_lower = input.lower()
        for keyword in INTERN_DATA_KEYWORDS:
            if keyword in text_lower:
                logger.debug(
                    "Input blocked for PII",
                    extra={"details": {"reason": "acesso_dados_internos"}},
                )
                return False
        return True

    async def _classify_with_llm(self, input: str) -> GuardrailResult:
        prompt = CLASSIFIER_PROMPT.format(mensagem=input)
        response = await self._text_generator.generate(prompt)

        category: str | None = None
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

    async def _guard_input(self, input: str) -> GuardrailResult:
        """Run input checks in ascendent cost order:
        Deterministic first, then LLM only if needed.
        """

        logger.debug(
            "Verifying input compliance",
            extra={"details": {"input_len": len(input)}},
        )

        if not self._check_prompt_injection(input):
            return GuardrailResult.block(
                "prompt_injection", "Não consigo processar essa solicitação."
            )

        if not self._check_pii_access(input):
            return GuardrailResult.block(
                "acesso_dados_internos",
                "Não tenho como compartilhar informações internas do sistema.",
            )

        try:
            return await self._classify_with_llm(input)
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

    @log_execution_time
    async def __call__(self, state: GraphState) -> dict[GraphStateKeys, Any]:
        user_input = state["messages"][-1]
        assert user_input.id is not None

        anonymized, pii_map = anonymize_input(user_input.text)
        logger.info(
            "Agent called",
            extra={
                "details": {
                    "name": self.name,
                    "input_anonymized": anonymized,
                }
            },
        )
        result = await self._guard_input(anonymized)

        if result.blocked:
            logger.info(
                "Agent response",
                extra={
                    "details": {
                        "from": self.name,
                        "status": "blocked",
                        "reason": result.blocked,
                    }
                },
            )
            return {
                GraphStateKeys.ROUTE: END,
                GraphStateKeys.CALLED_AGENTS: [self.name],
                GraphStateKeys.MESSAGES: [AIMessage(content=result.message)],
            }

        logger.info(
            "Agent response",
            extra={"details": {"from": self.name, "status": "approved"}},
        )
        return {
            GraphStateKeys.ROUTE: self._approved_route,
            GraphStateKeys.CALLED_AGENTS: [self.name],
            GraphStateKeys.PII_MAP: pii_map,
            GraphStateKeys.MESSAGES: [
                RemoveMessage(id=user_input.id),
                HumanMessage(content=result.message),
            ],
        }
