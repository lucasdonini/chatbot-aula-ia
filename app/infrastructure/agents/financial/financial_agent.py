import logging
from typing import Any, Dict

from langchain_core.messages import SystemMessage

from app.infrastructure.agents.llms import create_specialist
from app.infrastructure.agents.schema.graph_state import GraphState, GraphStateKeys
from app.infrastructure.agents.schema.specialist_output import FinancialOutput
from app.infrastructure.agents.temporal_context import build_temporal_context
from app.infrastructure.execution_time_logger import log_execution_time
from app.infrastructure.postgres.pg_connection import get_db
from app.infrastructure.repositories.transaction_repository import TransactionRepository
from app.services.transaction_service import TransactionService

from .financial_prompt import FINANCIAL_NODE_NAME, PROMPT
from .tools import (
    AddTransactionTool,
    DailyBalanceTool,
    DeleteTransactionTool,
    RestoreTransactionTool,
    SearchTransactionsTool,
    TotalBalanceTool,
    UpdateTransactionTool,
)

logger = logging.getLogger(__name__)


transaction_repository = TransactionRepository(session_factory=get_db)
transaction_service = TransactionService(repository=transaction_repository)
total_balance = TotalBalanceTool(service=transaction_service)
daily_balance = DailyBalanceTool(service=transaction_service)
search_transactions = SearchTransactionsTool(service=transaction_service)
add_transaction = AddTransactionTool(service=transaction_service)
update_transaction = UpdateTransactionTool(service=transaction_service)
delete_transaction = DeleteTransactionTool(service=transaction_service)
restore_transaction = RestoreTransactionTool(service=transaction_service)

TOOLS = [
    total_balance,
    daily_balance,
    search_transactions,
    add_transaction,
    update_transaction,
    delete_transaction,
    restore_transaction,
]


financial_agent = create_specialist(
    system_prompt=PROMPT,
    tools=TOOLS,
    response_format=FinancialOutput,
)


@log_execution_time
async def financial_node(state: GraphState) -> Dict[GraphStateKeys, Any]:
    input_text = state["messages"][-1].content[:500]
    logger.info(
        "Agent called",
        extra={"details": {"name": FINANCIAL_NODE_NAME, "input": input_text}},
    )
    request_state: GraphState = {
        **state,
        "messages": [
            SystemMessage(content=build_temporal_context()),
            *state["messages"],
        ],
    }
    response = await financial_agent.ainvoke(request_state)  # type: ignore[arg-type]
    last = (response.get("messages") or [None])[-1]
    output = last.content[:500] if last and last.content else "(tool call)"
    logger.info(
        "Agent response",
        extra={"details": {"from": FINANCIAL_NODE_NAME, "output": output}},
    )
    return {
        GraphStateKeys.MESSAGES: response.get("messages") or [],
        GraphStateKeys.CALLED_AGENTS: [FINANCIAL_NODE_NAME],
    }
