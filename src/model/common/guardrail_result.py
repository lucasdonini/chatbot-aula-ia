from pydantic import BaseModel, model_validator


class GuardrailResult(BaseModel):
    _allow_direct: bool = False
    blocked: bool
    reason: str
    message: str

    @model_validator(mode="wrap")
    @classmethod
    def _block_direct(cls, value, handler):
        raise TypeError("Direct Instantiation is not allowed")

    @classmethod
    def block(cls, reason: str, message: str) -> "GuardrailResult":
        return cls.model_construct(blocked=True, reason=reason, message=message)

    @classmethod
    def input_aproved(cls) -> "GuardrailResult":
        return cls.model_construct(blocked=False, reason="Input aproved", message="")

    @classmethod
    def output_aproved(cls, message: str) -> "GuardrailResult":
        return cls.model_construct(
            blocked=False, reason="Output aproved", message=message
        )
