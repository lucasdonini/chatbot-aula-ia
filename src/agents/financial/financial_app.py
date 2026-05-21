from langchain.agents import create_agent

from src.model.common.graph_state import GraphState, GraphStateKeys
from ..llms import specialist_llm
from .financial_prompts import FINANCIAL_PROMPT
from .tools import TOOLS

import logging

logger = logging.getLogger(__name__)
financial_app = create_agent(
    model=specialist_llm, system_prompt=FINANCIAL_PROMPT, tools=TOOLS
)


def financial_node(state: GraphState) -> dict:
    logger.info("Financial node invoked. State: %s", state)
    output = financial_app.invoke(
        {"messages": [{"role": "human", "content": state["input"]}]},
        config={"configurable": {"thread_id": {state["session_id"]}}},
    )
    text = output["messages"][-1].text
    logger.debug("Financial answered: %s", text)

    return {
        GraphStateKeys.SPECIALIST_OUTPUT: text,
        GraphStateKeys.CALLED_AGENTS: ["financeiro"],
    }
