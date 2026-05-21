from langchain.agents import create_agent

from src.model.common.graph_state import GraphState, GraphStateKeys
from ..llms import specialist_llm
from .agenda_prompts import AGENDA_PROMPT

import logging

logger = logging.getLogger(__name__)

agenda_app = create_agent(model=specialist_llm, system_prompt=AGENDA_PROMPT)


def agenda_node(state: GraphState) -> dict:
    logger.info("Agenda node invoked. State: %s", state)
    output = agenda_app.invoke(
        {"messages": [{"role": "human", "content": state["input"]}]},
        config={"configurable": {"thread_id": {state["session_id"]}}},
    )
    text = output["messages"][-1].text
    logger.debug("Agenda answered: %s", text)

    return {
        GraphStateKeys.SPECIALIST_OUTPUT: text,
        GraphStateKeys.CALLED_AGENTS: ["agenda"],
    }
