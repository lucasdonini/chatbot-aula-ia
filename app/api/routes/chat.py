from typing import Annotated

from fastapi import APIRouter, Depends
from pydantic import BaseModel

from app.api.dependencies import get_chat_session_service, get_graph, get_session_id
from app.application.ports.agent_graph import AgentGraph
from app.domain.model.chat_entry import HumanMessage
from app.services.chat_session_service import ChatSessionService

router = APIRouter(prefix="/chat")


class ChatRequest(BaseModel):
    message: str


@router.post("")
async def chat(
    graph: Annotated[AgentGraph, Depends(get_graph)],
    session_id: Annotated[str, Depends(get_session_id)],
    session_service: Annotated[ChatSessionService, Depends(get_chat_session_service)],
    user_input: ChatRequest,
) -> str:
    try:
        question = HumanMessage(content=user_input.message)
        await session_service.save_message(session_id=session_id, message=question)
        response = await graph.execute_agent_flux(question, session_id)
        await session_service.save_message(session_id=session_id, message=response)
        assert isinstance(response.content, str)
        return response.content
    except TimeoutError:
        raise
    except Exception as e:
        await session_service.save_error(session_id, e)
        raise
