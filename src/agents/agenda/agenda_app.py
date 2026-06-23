from langchain.agents import create_agent

from src.model.common.graph_state import GraphState, GraphStateKeys
from ..llms import specialist_llm
from .agenda_prompts import AGENDA_PROMPT

import logging

logger = logging.getLogger(__name__)

agenda_app = create_agent(model=specialist_llm, system_prompt=AGENDA_PROMPT)
