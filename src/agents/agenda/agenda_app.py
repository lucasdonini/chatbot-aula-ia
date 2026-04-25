from langchain.agents import create_agent

from ..llms import specialist_llm
from .agenda_prompts import AGENDA_PROMPT

agenda_app = create_agent(model=specialist_llm, system_prompt=AGENDA_PROMPT)
