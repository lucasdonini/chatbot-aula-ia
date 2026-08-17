from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

from app.infrastructure.agents.router.router_agent import (
    _filter_messages_for_router,
    _is_specialist_json,
)


class TestIsSpecialistJson:
    def test_valid_json_with_dominio(self):
        assert (
            _is_specialist_json('{"dominio": "financeiro", "resposta": "ok"}') is True
        )

    def test_valid_json_with_dominio_agenda(self):
        assert _is_specialist_json('{"dominio": "agenda"}') is True

    def test_valid_json_without_dominio(self):
        assert _is_specialist_json('{"outro": "valor"}') is False

    def test_not_json_string(self):
        assert _is_specialist_json("hello world") is False

    def test_not_string_int(self):
        assert _is_specialist_json(123) is False

    def test_not_string_none(self):
        assert _is_specialist_json(None) is False

    def test_not_string_dict(self):
        assert _is_specialist_json({"dominio": "teste"}) is False

    def test_malformed_json(self):
        assert _is_specialist_json("{dominio:}") is False

    def test_empty_dict(self):
        assert _is_specialist_json("{}") is False

    def test_whitespace_prefix_suffix(self):
        assert _is_specialist_json('  {"dominio": "agenda"}  ') is True


class TestFilterMessagesForRouter:
    def test_filters_out_foreign_tool_calls(self):
        msg = AIMessage(
            content="",
            tool_calls=[
                {"name": "total_balance", "args": {}, "id": "call_tb"},
            ],
        )
        result = _filter_messages_for_router([msg])
        assert len(result) == 0

    def test_keeps_own_tool_calls(self):
        msg = AIMessage(
            content="",
            tool_calls=[
                {"name": "search_history", "args": {"search": "test"}, "id": "call_sh"},
            ],
        )
        result = _filter_messages_for_router([msg])
        assert len(result) == 1

    def test_filters_specialist_json_aimessage(self):
        msg = AIMessage(content='{"dominio": "financeiro", "resposta": "saldo ok"}')
        result = _filter_messages_for_router([msg])
        assert len(result) == 0

    def test_keeps_non_specialist_aimessage(self):
        msg = AIMessage(content="Olá, como posso ajudar?")
        result = _filter_messages_for_router([msg])
        assert len(result) == 1
        assert result[0].content == "Olá, como posso ajudar?"

    def test_filters_toolmessage_for_foreign_tool(self):
        msgs = [
            AIMessage(
                content="",
                tool_calls=[
                    {"name": "total_balance", "args": {}, "id": "call_tb"},
                ],
            ),
            ToolMessage(content="5000", tool_call_id="call_tb"),
        ]
        result = _filter_messages_for_router(msgs)
        assert len(result) == 0

    def test_keeps_toolmessage_for_own_tool(self):
        msg = ToolMessage(content='[{"summary": "teste"}]', tool_call_id="call_sh")
        result = _filter_messages_for_router([msg])
        assert len(result) == 1

    def test_removes_foreign_calls_but_keeps_own_mixed(self):
        msg = AIMessage(
            content="",
            tool_calls=[
                {"name": "total_balance", "args": {}, "id": "call_tb"},
                {"name": "search_history", "args": {"search": "test"}, "id": "call_sh"},
            ],
        )
        result = _filter_messages_for_router([msg])
        assert len(result) == 1
        assert len(result[0].tool_calls) == 1
        assert result[0].tool_calls[0]["name"] == "search_history"

    def test_keeps_human_message(self):
        msg = HumanMessage(content="Qual meu saldo?")
        result = _filter_messages_for_router([msg])
        assert len(result) == 1

    def test_foreign_tool_call_without_id_is_ignored(self):
        msg = AIMessage(
            content="",
            tool_calls=[
                {"name": "total_balance", "args": {}, "id": "call_tb_no_id"},
            ],
        )
        result = _filter_messages_for_router([msg])
        assert len(result) == 0

    def test_complex_scenario(self):
        msgs = [
            HumanMessage(content="Qual meu saldo?"),
            AIMessage(
                content="",
                tool_calls=[
                    {"name": "total_balance", "args": {}, "id": "call_tb"},
                ],
            ),
            ToolMessage(content="5000", tool_call_id="call_tb"),
            AIMessage(content='{"dominio": "financeiro", "resposta": "R$ 5000"}'),
        ]
        result = _filter_messages_for_router(msgs)
        assert len(result) == 1
        assert isinstance(result[0], HumanMessage)
