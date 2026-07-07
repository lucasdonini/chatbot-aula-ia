from typing import Any, Literal, NoReturn, Optional

from pydantic import BaseModel, JsonValue, ValidatorFunctionWrapHandler, model_validator


class LegacyToolResponse(BaseModel):
    _allow_direct: bool = False
    status: str
    data: dict

    @model_validator(mode="wrap")
    @classmethod
    def _block_direct(
        cls, value: Any, handler: ValidatorFunctionWrapHandler
    ) -> NoReturn:
        raise TypeError(
            "Direct instantiation is not allowed. "
            "Use DatabaseToolResponse[.ok()/.error()/.exception()] instead."
        )

    @classmethod
    def ok(cls, data: dict) -> "LegacyToolResponse":
        return cls.model_construct(status="ok", data=data)

    @classmethod
    def error(cls, msg: str, details: Optional[dict] = None) -> "LegacyToolResponse":
        data = {"message": msg, "details": details if details else {}}
        return cls.model_construct(status="error", data=data)

    @classmethod
    def exception(cls, e: Exception) -> "LegacyToolResponse":
        return cls.error(str(e))


class ToolError(BaseModel):
    message: str
    details: dict[str, JsonValue] = {}


class ToolSuccess[T: BaseModel](BaseModel):
    status: Literal["ok"] = "ok"
    data: T


class ToolFailure(BaseModel):
    status: Literal["error"] = "error"
    error: ToolError


type ToolResponse[T: BaseModel] = ToolSuccess[T] | ToolFailure
