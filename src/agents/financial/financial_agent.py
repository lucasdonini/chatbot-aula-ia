import logging
from typing import Any, Dict

from langchain.agents import create_agent

from src.infrastructure.execution_time_logger import log_execution_time
from src.infrastructure.postgres.pg_connection import get_db
from src.infrastructure.repositories.transaction_repository import TransactionRepository
from src.model.graph_state import GraphState, GraphStateKeys
from src.model.specialist_output import FinancialOutput
from src.services.transaction_service import TransactionService

from ..llms import specialist_llm
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


financial_agent = create_agent(
    model=specialist_llm,  # type: ignore[arg-type]
    system_prompt=PROMPT,
    tools=TOOLS,
    response_format=FinancialOutput,
)

financial_agent.ainvoke = log_execution_time(  # type: ignore[assignment]
    financial_agent.ainvoke,  # type: ignore[arg-type]
    logger=logger,
)


async def financial_node(state: GraphState) -> Dict[GraphStateKeys, Any]:
    input_text = state["messages"][-1].content[:500]
    logger.info(
        "Agent called",
        extra={"details": {"name": FINANCIAL_NODE_NAME, "input": input_text}},
    )
    response = await financial_agent.ainvoke(state)  # type: ignore[arg-type]
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
