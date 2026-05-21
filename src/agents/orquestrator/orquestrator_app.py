from langchain.agents import create_agent

from src.model.common.graph_state import GraphState, GraphStateKeys
from ..llms import fast_llm
from .orquestrator_prompts import ORQUESTRATOR_PROMPT

import logging

logger = logging.getLogger(__name__)
orquestrator_app = create_agent(model=fast_llm, system_prompt=ORQUESTRATOR_PROMPT)


def orquestrator_node(state: GraphState) -> dict:
    logger.info("Orquestrator node invoked. State: %s", state)
    output = orquestrator_app.invoke(
        {"messages": [{"role": "human", "content": state["specialist_output"]}]},
        config={"configurable": {"thread_id": {state["session_id"]}}},
    )
    text = output["messages"][-1].text
    logger.debug("Orquestrator answered: %s", text)

    return {
        GraphStateKeys.FINAL_OUTPUT: text,
        GraphStateKeys.CALLED_AGENTS: ["orquestrador"],
    }
