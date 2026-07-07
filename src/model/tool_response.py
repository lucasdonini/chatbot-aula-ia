from typing import Any, NoReturn, Optional

from pydantic import BaseModel, ValidatorFunctionWrapHandler, model_validator


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
