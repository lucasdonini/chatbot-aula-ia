from typing import Annotated

from pydantic import BaseModel, Field


class SessionFinalizationResponse(BaseModel):
    session_id: Annotated[str, Field(description="The id of the finalized session")]
    session_summary: Annotated[
        str | None,
        Field(
            description=(
                "The summary of all messages under the target session. "
                "If the session has already been finalized, "
                "returns the summary from database. "
                "If the session has no messages or does not exist, returns null."
            )
        ),
    ]
