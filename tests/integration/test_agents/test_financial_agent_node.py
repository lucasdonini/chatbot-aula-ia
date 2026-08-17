import pytest
from langchain_core.messages import AIMessage, HumanMessage

from app.infrastructure.agents.financial.financial_agent import financial_node
from app.infrastructure.agents.financial.financial_prompt import FINANCIAL_NODE_NAME
from app.infrastructure.agents.schema.graph_state import GraphState

pytestmark = [
    pytest.mark.integration,
    pytest.mark.usefixtures("apply_migrations"),
]


class TestFinancialAgentNode:
    async def _run_node(self) -> dict:
        state = GraphState(
            messages=[HumanMessage(content="qual meu saldo?")],
            called_agents=[],
            route="financial",
            pii_map={},
        )
        return await financial_node(state)

    @pytest.mark.asyncio
    async def test_calls_total_balance_tool(
        self, mock_gemini_ainvoke, seed_transactions
    ):
        from langchain_core.messages import ToolCall

        mock_gemini_ainvoke.return_value = AIMessage(
            content="",
            tool_calls=[
                ToolCall(name="total_balance", args={}, id="call_tb_1"),
            ],
        )

        result = await self._run_node()

        assert FINANCIAL_NODE_NAME in result["called_agents"]
        assert len(result["messages"]) > 0

    @pytest.mark.asyncio
    async def test_calls_daily_balance_tool(
        self, mock_gemini_ainvoke, seed_transactions
    ):
        mock_gemini_ainvoke.return_value = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "daily_balance",
                    "args": {"target_date": "2026-06-01"},
                    "id": "call_db_1",
                }
            ],
        )

        result = await self._run_node()

        assert FINANCIAL_NODE_NAME in result["called_agents"]

    @pytest.mark.asyncio
    async def test_calls_search_tool(self, mock_gemini_ainvoke, seed_transactions):
        mock_gemini_ainvoke.return_value = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "search_transactions",
                    "args": {"category": "comida", "limit": 10},
                    "id": "call_st_1",
                }
            ],
        )

        result = await self._run_node()

        assert FINANCIAL_NODE_NAME in result["called_agents"]

    @pytest.mark.asyncio
    async def test_calls_add_tool(self, mock_gemini_ainvoke, seed_transactions):
        mock_gemini_ainvoke.return_value = AIMessage(
            content="",
            tool_calls=[
                {
                    "name": "add_transaction",
                    "args": {
                        "amount": 100.0,
                        "category": "comida",
                        "transaction_type": "EXPENSE",
                        "source_text": "almoço",
                    },
                    "id": "call_at_1",
                }
            ],
        )

        result = await self._run_node()

        assert FINANCIAL_NODE_NAME in result["called_agents"]

    @pytest.mark.asyncio
    async def test_direct_response_no_tool_call(
        self, mock_gemini_ainvoke, seed_transactions
    ):
        mock_gemini_ainvoke.return_value = AIMessage(
            content="Seu saldo atual é de R$ 7.600,00.",
            tool_calls=[],
        )

        result = await self._run_node()

        assert len(result["messages"]) > 0
