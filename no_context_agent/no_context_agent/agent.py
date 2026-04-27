"""
Baseline agent — no memory tools, no compaction, plain system prompt.
"""

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm


SYSTEM_INSTRUCTION = "You are a friendly, helpful AI assistant. Write only the conversational reply — never your reasoning or notes."

agent = Agent(
    name="no_ce_agent",
    model=LiteLlm(
        model="ollama_chat/gemma4",
        think=False,  # disable Ollama thinking to prevent reasoning leaking into responses
    ),
    instruction=SYSTEM_INSTRUCTION,
)
