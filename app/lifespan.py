import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from .infrastructure.agents import build_agent_graph
from .infrastructure.clock import SystemClock
from .infrastructure.llms import fast_llm
from .infrastructure.logger import (
    bind_session_context,
    bind_trace_context,
    clear_session_interactions,
    create_logger,
    increment_interaction,
    setup_logger,
)
from .infrastructure.mongodb.client import MongoManager
from .infrastructure.postgres.pg_connection import PostgresManager
from .infrastructure.postgres.repositories.transaction_repository import (
    SQLAlchemyTransactionRepository,
)
from .infrastructure.settings import settings
from .infrastructure.text_generator import LLMTextGenerator
from .services.chat_history_service import ChatHistoryService
from .services.chat_session_service import ChatSessionService
from .services.session_summary_service import SessionSummaryService
from .services.transaction_service import TransactionService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logger()
    settings.validate_llm_api_keys()

    mongo_manager = MongoManager(settings=settings)
    await mongo_manager.init_database()
    postgres_manager = PostgresManager(settings.postgres_url.get_secret_value())
    clock = SystemClock(settings.app_timezone)

    text_generator = LLMTextGenerator(fast_llm)
    summary_service = SessionSummaryService(
        text_generator,
        logger=create_logger(SessionSummaryService.__module__),
    )
    session_service = ChatSessionService(
        summary_service,
        logger=create_logger(ChatSessionService.__module__),
        clock=clock,
    )

    session_id = str(uuid.uuid4())
    with bind_session_context(session_id):
        await session_service.init_session(session_id)

    transaction_repository = SQLAlchemyTransactionRepository(
        session_factory=postgres_manager.session_factory
    )
    transaction_service = TransactionService(
        repository=transaction_repository,
        logger=create_logger(TransactionService.__module__),
    )
    chat_history_service = ChatHistoryService(
        logger=create_logger(ChatHistoryService.__module__),
    )

    graph = build_agent_graph(
        transaction_service=transaction_service,
        chat_history_service=chat_history_service,
        text_generator=text_generator,
        logger_factory=create_logger,
        trace_context_factory=bind_trace_context,
        interaction_incrementer=increment_interaction,
        clock=clock,
        execution_timeout_seconds=settings.agent_execution_timeout_seconds,
    )

    app.state.session_summary_service = summary_service
    app.state.chat_session_service = session_service
    app.state.session_id = session_id
    app.state.graph = graph

    try:
        yield
    finally:
        try:
            with bind_session_context(session_id):
                await session_service.finalize_session(session_id)
        finally:
            clear_session_interactions(session_id)
            await postgres_manager.dispose()
