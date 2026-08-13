import pytest

from app.model.guardrail_result import GuardrailResult


class TestGuardrailResult:
    def test_direct_instantiation_blocked(self):
        with pytest.raises(TypeError):
            GuardrailResult(blocked=True, reason="test", message="msg")

    def test_block(self):
        result = GuardrailResult.block("prompt_injection", "Blocked")
        assert result.blocked is True
        assert result.reason == "prompt_injection"
        assert result.message == "Blocked"

    def test_input_aproved(self):
        result = GuardrailResult.input_aproved("mensagem anonimizada")
        assert result.blocked is False
        assert result.reason == "Input aproved"
        assert result.message == "mensagem anonimizada"

    def test_output_aproved(self):
        result = GuardrailResult.output_aproved("resposta final")
        assert result.blocked is False
        assert result.reason == "Output aproved"
        assert result.message == "resposta final"

    def test_block_is_blocked(self):
        result = GuardrailResult.block("motivo", "msg")
        assert result.blocked is True

    def test_input_aproved_is_not_blocked(self):
        result = GuardrailResult.input_aproved("msg")
        assert result.blocked is False

    def test_output_aproved_is_not_blocked(self):
        result = GuardrailResult.output_aproved("msg")
        assert result.blocked is False

    def test_block_reason_is_stored(self):
        result = GuardrailResult.block("acesso_dados_internos", "Negado")
        assert result.reason == "acesso_dados_internos"

    def test_multiple_block_calls(self):
        r1 = GuardrailResult.block("a", "msg1")
        r2 = GuardrailResult.block("b", "msg2")
        assert r1 is not r2
        assert r1.reason == "a"
        assert r2.reason == "b"
