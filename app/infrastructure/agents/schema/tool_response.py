from typing import Literal

from pydantic import BaseModel, JsonValue


class ToolSuccess[T: BaseModel](BaseModel):
    status: Literal["ok"] = "ok"
    data: T


class ToolFailure(BaseModel):
    status: Literal["error"] = "error"
    error: str
    details: dict[str, JsonValue] = {}

    @classmethod
    def exception(cls, e: Exception) -> "ToolFailure":
        return cls.model_construct(
            error="Exception raised", details={"exception": str(e)}
        )


type ToolResponse[T: BaseModel] = ToolSuccess[T] | ToolFailure
