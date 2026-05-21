from langchain.agents import create_agent

from src.model.common.graph_state import GraphState, GraphStateKeys
from ..llms import fast_llm
from .faq_reader_prompts import FAQ_PROMPT
from .tools import TOOLS

import logging

logger = logging.getLogger(__name__)
faq_reader_app = create_agent(model=fast_llm, system_prompt=FAQ_PROMPT, tools=TOOLS)


def faq_reader_node(state: GraphState) -> dict:
    logger.info("Faq Reader node invoked. State: %s", state)
    output = faq_reader_app.invoke(
        {"messages": [{"role": "human", "content": state["input"]}]},
        config={"configurable": {"thread_id": {state["session_id"]}}},
    )
    text = output["messages"][-1].text
    logger.debug("Faq Reader answered: %s", text)

    return {
        GraphStateKeys.SPECIALIST_OUTPUT: text,
        # bypassa o orquestrador
        GraphStateKeys.FINAL_OUTPUT: text,
        GraphStateKeys.CALLED_AGENTS: ["faq"],
    }
