from langchain.agents import create_agent

from .orquestrator_prompts import ORQUESTRATOR_PROMPT
from ..llms import fast_llm

orquestrator_app = create_agent(model=fast_llm, system_prompt=ORQUESTRATOR_PROMPT)
