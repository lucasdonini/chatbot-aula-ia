from langgraph.graph import END

from app.application.ports.logger import (
    InteractionIncrementer,
    LoggerFactory,
    TraceContextFactory,
)
from app.application.ports.text_generator import TextGenerator
from app.infrastructure.llms import fast_llm, llm_gemini, llm_groq
from app.services.chat_history_service import ChatHistoryService
from app.services.transaction_service import TransactionService

from ._core.factories.langchain_agent_factory import LangChainAgentFactory
from ._core.middleware import FallbackOn429Middleware
from ._core.specialist import SpecialistRegistration
from .agenda import AgendaAgentNode
from .faq import FAQAgentNode
from .faq.tools import create_faq_retriever
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
    chat_history_service: ChatHistoryService,
    text_generator: TextGenerator,
    logger_factory: LoggerFactory,
    trace_context_factory: TraceContextFactory,
    interaction_incrementer: InteractionIncrementer,
    execution_timeout_seconds: float = 120.0,
) -> AgentGraphImpl:
    specialist_fallback = FallbackOn429Middleware(
        llm_groq,
        logger=logger_factory(FallbackOn429Middleware.__module__),
    )

    financial_tools = (
        TotalBalanceTool(
            service=transaction_service,
            logger=logger_factory(TotalBalanceTool.__module__),
        ),
        DailyBalanceTool(
            service=transaction_service,
            logger=logger_factory(DailyBalanceTool.__module__),
        ),
        SearchTransactionsTool(
            service=transaction_service,
            logger=logger_factory(SearchTransactionsTool.__module__),
        ),
        AddTransactionTool(
            service=transaction_service,
            logger=logger_factory(AddTransactionTool.__module__),
        ),
        UpdateTransactionTool(
            service=transaction_service,
            logger=logger_factory(UpdateTransactionTool.__module__),
        ),
        DeleteTransactionTool(
            service=transaction_service,
            logger=logger_factory(DeleteTransactionTool.__module__),
        ),
        RestoreTransactionTool(
            service=transaction_service,
            logger=logger_factory(RestoreTransactionTool.__module__),
        ),
    )
    financial = FinancialAgentNode(
        LangChainAgentFactory(
            llm=llm_gemini,
            tools=financial_tools,
            middlewares=(specialist_fallback,),
        ),
        logger=logger_factory(FinancialAgentNode.__module__),
    )
    agenda = AgendaAgentNode(
        LangChainAgentFactory(
            llm=llm_gemini,
            middlewares=(specialist_fallback,),
        ),
        logger=logger_factory(AgendaAgentNode.__module__),
    )
    faq = FAQAgentNode(
        LangChainAgentFactory(
            llm=fast_llm,
            tools=(
                create_faq_retriever(
                    logger_factory("app.infrastructure.agents.faq.tools.pdf_rag")
                ),
            ),
        ),
        logger=logger_factory(FAQAgentNode.__module__),
    )
    orquestrator = OrquestratorAgentNode(
        LangChainAgentFactory(llm=fast_llm),
        logger=logger_factory(OrquestratorAgentNode.__module__),
    )

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

    history_tool = SearchHistoryTool(
        service=chat_history_service,
        logger=logger_factory(SearchHistoryTool.__module__),
    )
    router = RouterAgentNode(
        agent_factory=LangChainAgentFactory(
            llm=fast_llm,
            tools=(history_tool,),
        ),
        logger=logger_factory(RouterAgentNode.__module__),
        specialists=specialists,
        allowed_tool_names=(history_tool.name,),
    )
    input_guardrail = InputGuardrailNode(
        text_generator=text_generator,
        approved_route=router.name,
        logger=logger_factory(InputGuardrailNode.__module__),
    )
    output_guardrail = OutputGuardrailNode(
        text_generator,
        logger=logger_factory(OutputGuardrailNode.__module__),
    )

    return AgentGraphImpl(
        input_guardrail=input_guardrail,
        router=router,
        specialists=specialists,
        orquestrator=orquestrator,
        output_guardrail=output_guardrail,
        execution_timeout_seconds=execution_timeout_seconds,
        logger=logger_factory(AgentGraphImpl.__module__),
        trace_context_factory=trace_context_factory,
        interaction_incrementer=interaction_incrementer,
    )
