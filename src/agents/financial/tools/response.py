from pydantic import BaseModel, model_validator


class DatabaseToolResponse(BaseModel):
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
    def ok(cls, data: dict) -> "DatabaseToolResponse":
        return cls.model_construct(status="ok", data=data)

    @classmethod
    def error(cls, msg: str) -> "DatabaseToolResponse":
        return cls.model_construct(status="error", data={"message": msg})

    @classmethod
    def exception(cls, e: Exception) -> "DatabaseToolResponse":
        return cls.error(str(e))
