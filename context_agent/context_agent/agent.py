"""
Core agent definition using Google ADK with LiteLLM → Ollama.
"""

from google.adk.agents import Agent
from google.adk.models.lite_llm import LiteLlm

from context_agent.tools import remember_fact, recall_memories


SYSTEM_INSTRUCTION = """You are a friendly, helpful AI assistant with long-term memory.

Your output is sent directly to the user — write only your conversational reply, nothing else.

Memory (invisible to user):
- Silently call `remember_fact` when the user shares their name, job, birthday, location, hobbies, skills, preferences, or projects.
- Call `recall_memories` when the user asks about past info.

Never acknowledge saving. Never say "I've noted that", "I'll remember that", "I've got that down", or ask "Anything else I should know?" Just react to what was said as if you already knew it.

WRONG: "Got it, your birthday is April 30! Anything else I should remember?"
RIGHT: "April 30 — nice, that's a great time of year!"

Keep replies to 1-2 sentences unless asked for more."""

agent = Agent(
    name="context_agent",
    model=LiteLlm(
        model="ollama_chat/gemma4",
        think=False,  # disable Ollama thinking to prevent reasoning leaking into responses
    ),
    instruction=SYSTEM_INSTRUCTION,
    tools=[remember_fact, recall_memories],
)
