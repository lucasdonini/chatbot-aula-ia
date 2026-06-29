import logging
from typing import Any, Dict

from langchain.agents import create_agent

from src.infrastructure.execution_time_logger import log_execution_time
from src.model.graph_state import GraphState, GraphStateKeys

from ..llms import fast_llm
from .faq_prompt import FAQ_NODE_NAME, PROMPT
from .tools import TOOLS

logger = logging.getLogger(__name__)

faq_agent = create_agent(
    model=fast_llm,  # type: ignore[arg-type]
    system_prompt=PROMPT,
    tools=TOOLS,
)

faq_agent.ainvoke = log_execution_time(  # type: ignore[assignment]
    faq_agent.ainvoke,  # type: ignore[arg-type]
    logger=logger,
)


async def faq_node(state: GraphState) -> Dict[GraphStateKeys, Any]:
    logger.info("─" * 50)
    logger.info(" [NODE] FAQ ")
    logger.info(" Input: %s", state["messages"][-1].content[:500])
    response = await faq_agent.ainvoke(state)  # type: ignore[arg-type]
    last = (response.get("messages") or [None])[-1]
    output = last.content[:500] if last and last.content else "(tool call)"
    logger.info(" Output: %s", output)
    logger.info("─" * 50)
    return {
        GraphStateKeys.MESSAGES: response.get("messages") or [],
        GraphStateKeys.CALLED_AGENTS: [FAQ_NODE_NAME],
    }
