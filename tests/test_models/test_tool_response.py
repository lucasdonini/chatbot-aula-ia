import pytest

from src.model.tool_response import LegacyToolResponse


class TestToolResponse:
    def test_direct_instantiation_blocked(self):
        with pytest.raises(TypeError):
            LegacyToolResponse(status="ok", data={})

    def test_ok(self):
        response = LegacyToolResponse.ok({"saldo": 1000.0})
        assert response.status == "ok"
        assert response.data == {"saldo": 1000.0}

    def test_ok_empty_data(self):
        response = LegacyToolResponse.ok({})
        assert response.status == "ok"
        assert response.data == {}

    def test_error(self):
        response = LegacyToolResponse.error("Something went wrong")
        assert response.status == "error"
        assert response.data["message"] == "Something went wrong"
        assert response.data["details"] == {}

    def test_error_with_details(self):
        response = LegacyToolResponse.error("Error", {"code": 500})
        assert response.status == "error"
        assert response.data["message"] == "Error"
        assert response.data["details"] == {"code": 500}

    def test_exception(self):
        exc = ValueError("invalid value")
        response = LegacyToolResponse.exception(exc)
        assert response.status == "error"
        assert response.data["message"] == "invalid value"

    def test_ok_is_not_blocked(self):
        response = LegacyToolResponse.ok({"key": "val"})
        assert response.status == "ok"

    def test_error_is_not_ok(self):
        response = LegacyToolResponse.error("fail")
        assert response.status != "ok"

    def test_multiple_ok_calls_return_different_instances(self):
        r1 = LegacyToolResponse.ok({"a": 1})
        r2 = LegacyToolResponse.ok({"b": 2})
        assert r1 is not r2
        assert r1.data == {"a": 1}
        assert r2.data == {"b": 2}
