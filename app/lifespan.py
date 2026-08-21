import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from .infrastructure.agents import build_agent_graph
from .infrastructure.llms import fast_llm
from .infrastructure.logger import set_session_context, setup_logger
from .infrastructure.mongodb.client import MongoManager
from .infrastructure.postgres.pg_connection import get_db
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

    text_generator = LLMTextGenerator(fast_llm)
    summary_service = SessionSummaryService(text_generator)
    session_service = ChatSessionService(summary_service)

    session_id = str(uuid.uuid4())
    await session_service.init_session(session_id)
    set_session_context(session_id)

    transaction_repository = SQLAlchemyTransactionRepository(session_factory=get_db)
    transaction_service = TransactionService(repository=transaction_repository)

    graph = build_agent_graph(
        transaction_service=transaction_service,
        text_generator=text_generator,
    )

    app.state.session_summary_service = summary_service
    app.state.session_id = session_id
    app.state.graph = graph

    yield

    await session_service.finalize_session(session_id)
