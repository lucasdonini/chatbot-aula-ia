import uuid
from typing import Annotated

from fastapi import APIRouter, Depends
from langchain_core.messages import HumanMessage
from pydantic import BaseModel

from app.agents.graph import execute_agent_flux
from app.dependencies import get_chat_session_service, get_session_id
from app.services.chat_session_service import ChatSessionService

router = APIRouter(prefix="/chat")


class ChatRequest(BaseModel):
    message: str


@router.post("")
async def chat(
    session_id: Annotated[str, Depends(get_session_id)],
    session_service: Annotated[ChatSessionService, Depends(get_chat_session_service)],
    user_input: ChatRequest,
) -> str:
    try:
        question = HumanMessage(id=str(uuid.uuid4()), content=user_input.message)
        await session_service.save_message(session_id=session_id, message=question)
        response = await execute_agent_flux(question, session_id)
        await session_service.save_message(session_id=session_id, message=response)
        assert isinstance(response.content, str)
        return response.content
    except Exception as e:
        await session_service.save_error(session_id, e)
        raise
