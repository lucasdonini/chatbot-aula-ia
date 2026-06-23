from langchain.agents import create_agent

from src.model.common.graph_state import GraphState, GraphStateKeys
from ..llms import fast_llm
from .faq_reader_prompts import FAQ_PROMPT
from .tools import TOOLS

import logging

logger = logging.getLogger(__name__)
faq_reader_app = create_agent(model=fast_llm, system_prompt=FAQ_PROMPT, tools=TOOLS)
