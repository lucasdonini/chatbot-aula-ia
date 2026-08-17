import uuid
from contextlib import asynccontextmanager
from typing import AsyncGenerator

from fastapi import FastAPI

from .agents.llms import fast_llm
from .infrastructure.logger import set_session_context, setup_logger
from .infrastructure.mongodb.client import MongoManager
from .infrastructure.settings import settings
from .services.chat_session_service import ChatSessionService
from .services.session_summary_service import SessionSummaryService


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    setup_logger()
    settings.validate_llm_api_keys()

    mongo_manager = MongoManager(settings=settings)
    await mongo_manager.init_database()

    summary_service = SessionSummaryService(fast_llm)
    session_service = ChatSessionService(summary_service)

    session_id = str(uuid.uuid4())
    await session_service.init_session(session_id)
    set_session_context(session_id)

    app.state.fast_llm = fast_llm
    app.state.session_id = session_id

    yield

    await session_service.finalize_session(session_id)
