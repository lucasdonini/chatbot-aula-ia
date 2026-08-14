from typing import Annotated, cast

from fastapi import Depends, Request

from .services.chat_session_service import ChatSessionService
from .services.session_summary_service import SessionSummaryService


def get_session_id(request: Request) -> str:
    return cast(str, request.app.state.session_id)


def get_session_summary_service() -> SessionSummaryService:
    return SessionSummaryService()


def get_chat_session_service(
    session_summary_service: Annotated[
        SessionSummaryService,
        Depends(get_session_summary_service),
    ],
) -> ChatSessionService:
    return ChatSessionService(session_summary_service)
