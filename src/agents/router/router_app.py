from langchain.agents import create_agent
from langgraph.checkpoint.memory import MemorySaver

from .router_prompts import ROUTER_PROMPT
from ..llms import fast_llm

router_memory = MemorySaver()
router_app = create_agent(
    model=fast_llm,
    system_prompt=ROUTER_PROMPT,
    checkpointer=router_memory,
)
