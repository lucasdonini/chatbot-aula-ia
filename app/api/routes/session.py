from typing import Annotated

from fastapi import APIRouter, Depends

from app.services.chat_session_service import ChatSessionService

from ..dependencies import bind_session_logging_context, get_chat_session_service
from ..schemas.session import SessionFinalizationResponse

router = APIRouter(
    prefix="/session", dependencies=[Depends(bind_session_logging_context)]
)


@router.post("/{session_id}/finalize")
async def finalize_session(
    session_id: str,
    session_service: Annotated[ChatSessionService, Depends(get_chat_session_service)],
) -> SessionFinalizationResponse:
    summary = await session_service.finalize_session(session_id)
    return SessionFinalizationResponse(session_id=session_id, session_summary=summary)
