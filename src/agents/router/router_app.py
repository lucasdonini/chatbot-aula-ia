from langchain.agents import create_agent

from src.model.common.graph_state import GraphState, GraphStateKeys
from ..llms import fast_llm
from .router_prompts import ROUTER_PROMPT

import logging

logger = logging.getLogger(__name__)

router_app = create_agent(
    model=fast_llm,
    system_prompt=ROUTER_PROMPT,
)


def router_node(state: GraphState) -> dict:
    logger.info("Router node invoked. State: %s", state)
    output = router_app.invoke(
        {"messages": [{"role": "human", "content": state["input"]}]},
        config={"configurable": {"thread_id": state["session_id"]}},
    )
    text = output["messages"][-1].text
    logger.debug("Router answered: %s", text)

    # Resposta direta (saudação, fora de escopo): já escreve no campo final
    if not text.strip().startswith("ROUTE="):
        return {
            GraphStateKeys.CALLED_AGENTS: ["roteador"],
            GraphStateKeys.FINAL_OUTPUT: text,
        }

    # Encaminhamento: sobrescreve input com o protocolo para o especialista
    return {
        GraphStateKeys.INPUT: text,
        GraphStateKeys.CALLED_AGENTS: ["roteador"],
    }
