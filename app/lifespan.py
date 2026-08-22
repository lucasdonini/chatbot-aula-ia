import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from .infrastructure.agents import build_agent_graph
from .infrastructure.llms import fast_llm
from .infrastructure.logger import create_logger, set_session_context, setup_logger
from .infrastructure.mongodb.client import MongoManager
from .infrastructure.postgres.pg_connection import PostgresManager
from .infrastructure.postgres.repositories.transaction_repository import (
    SQLAlchemyTransactionRepository,
)
from .infrastructure.settings import settings
from .infrastructure.text_generator import LLMTextGenerator
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

    text_generator = LLMTextGenerator(fast_llm)
    summary_service = SessionSummaryService(
        text_generator,
        logger=create_logger(SessionSummaryService.__module__),
    )
    session_service = ChatSessionService(
        summary_service,
        logger=create_logger(ChatSessionService.__module__),
    )

    session_id = str(uuid.uuid4())
    await session_service.init_session(session_id)
    set_session_context(session_id)

    transaction_repository = SQLAlchemyTransactionRepository(
        session_factory=postgres_manager.session_factory
    )
    transaction_service = TransactionService(
        repository=transaction_repository,
        logger=create_logger(TransactionService.__module__),
    )

    graph = build_agent_graph(
        transaction_service=transaction_service,
        text_generator=text_generator,
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
            await session_service.finalize_session(session_id)
        finally:
            await postgres_manager.dispose()
