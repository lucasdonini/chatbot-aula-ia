from langgraph.graph import END

from app.application.ports.text_generator import TextGenerator
from app.infrastructure.llms import fast_llm, llm_gemini, llm_groq
from app.services.chat_history_service import ChatHistoryService
from app.services.transaction_service import TransactionService

from ._core.factories.langchain_agent_factory import LangChainAgentFactory
from ._core.middleware import FallbackOn429Middleware
from ._core.specialist import SpecialistRegistration
from .agenda import AgendaAgentNode
from .faq import FAQAgentNode
from .faq.tools import faq_retriever
from .financial import FinancialAgentNode
from .financial.tools import (
    AddTransactionTool,
    DailyBalanceTool,
    DeleteTransactionTool,
    RestoreTransactionTool,
    SearchTransactionsTool,
    TotalBalanceTool,
    UpdateTransactionTool,
)
from .graph import AgentGraphImpl
from .guardrails import InputGuardrailNode, OutputGuardrailNode
from .orquestrator import OrquestratorAgentNode
from .router import RouterAgentNode
from .router.tools import SearchHistoryTool


def build_agent_graph(
    *,
    transaction_service: TransactionService,
    text_generator: TextGenerator,
) -> AgentGraphImpl:
    specialist_fallback = FallbackOn429Middleware(llm_groq)

    financial_tools = (
        TotalBalanceTool(service=transaction_service),
        DailyBalanceTool(service=transaction_service),
        SearchTransactionsTool(service=transaction_service),
        AddTransactionTool(service=transaction_service),
        UpdateTransactionTool(service=transaction_service),
        DeleteTransactionTool(service=transaction_service),
        RestoreTransactionTool(service=transaction_service),
    )
    financial = FinancialAgentNode(
        LangChainAgentFactory(
            llm=llm_gemini,
            tools=financial_tools,
            middlewares=(specialist_fallback,),
        )
    )
    agenda = AgendaAgentNode(
        LangChainAgentFactory(
            llm=llm_gemini,
            middlewares=(specialist_fallback,),
        )
    )
    faq = FAQAgentNode(
        LangChainAgentFactory(
            llm=fast_llm,
            tools=(faq_retriever,),
        )
    )
    orquestrator = OrquestratorAgentNode(LangChainAgentFactory(llm=fast_llm))

    specialists = (
        SpecialistRegistration(
            node=financial,
            description=(
                "gastos, receitas, dívidas, orçamento, metas, saldo e investimentos"
            ),
            destination=orquestrator.name,
        ),
        SpecialistRegistration(
            node=agenda,
            description=(
                "compromissos, eventos, lembretes, tarefas, horários e conflitos"
            ),
            destination=orquestrator.name,
        ),
        SpecialistRegistration(
            node=faq,
            description=(
                "regras, políticas, termos, privacidade, segurança e comportamento "
                "do sistema"
            ),
            destination=END,
        ),
    )

    history_tool = SearchHistoryTool(service=ChatHistoryService())
    router = RouterAgentNode(
        agent_factory=LangChainAgentFactory(
            llm=fast_llm,
            tools=(history_tool,),
        ),
        specialists=specialists,
        allowed_tool_names=(history_tool.name,),
    )
    input_guardrail = InputGuardrailNode(
        text_generator=text_generator,
        approved_route=router.name,
    )
    output_guardrail = OutputGuardrailNode(text_generator)

    return AgentGraphImpl(
        input_guardrail=input_guardrail,
        router=router,
        specialists=specialists,
        orquestrator=orquestrator,
        output_guardrail=output_guardrail,
    )
