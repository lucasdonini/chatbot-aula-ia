from pydantic import BaseModel, model_validator
from typing import Optional


class ToolResponse(BaseModel):
    _allow_direct: bool = False
    status: str
    data: dict

    @model_validator(mode="wrap")
    @classmethod
    def _block_direct(cls, value, handler):
        raise TypeError(
            "Direct instantiation is not allowed. Use DatabaseToolResponse[.ok()/.error()/.exception()] instead."
        )

    @classmethod
    def ok(cls, data: dict) -> "ToolResponse":
        return cls.model_construct(status="ok", data=data)

    @classmethod
    def error(cls, msg: str, details: Optional[dict] = None) -> "ToolResponse":
        data = {"message": msg, "details": details if details else {}}
        return cls.model_construct(status="error", data=data)

    @classmethod
    def exception(cls, e: Exception) -> "ToolResponse":
        return cls.error(str(e))
