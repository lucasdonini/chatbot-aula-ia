from langchain.agents import create_agent

from ..llms import specialist_llm
from .financial_prompts import FINANCIAL_PROMPT
from .tools import TOOLS

import logging

logger = logging.getLogger(__name__)
financial_app = create_agent(
    model=specialist_llm, system_prompt=FINANCIAL_PROMPT, tools=TOOLS
)
