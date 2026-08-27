from typing import Annotated

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    message: Annotated[
        str, Field(description="The question made to the agent.", min_length=1)
    ]


class ChatResponse(BaseModel):
    session_id: Annotated[str, Field(description="The id of the current session.")]
    content: Annotated[str, Field(description="The content of the agent's response.")]
