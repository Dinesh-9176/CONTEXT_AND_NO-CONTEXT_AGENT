"""
App wrapper — configures Conversation Compaction via EventsCompactionConfig.

NOTE on Context Caching:
- ADK's ContextCacheConfig is a Google Gemini API feature — does NOT work with Ollama/LiteLLM.
- For Ollama, KV caching is AUTOMATIC and implicit. Ollama caches the prompt prefix in
  VRAM as long as the model stays loaded. We rely on the stable system instruction prefix
  and keep_alive=-1 to maximise cache hits.
"""

from google.adk.apps.app import App, EventsCompactionConfig
from google.adk.apps.llm_event_summarizer import LlmEventSummarizer
from google.adk.models.lite_llm import LiteLlm

from context_agent.agent import agent


def create_app() -> App:
    summarizer_llm = LiteLlm(model="ollama_chat/gemma4", think=False)
    summarizer = LlmEventSummarizer(llm=summarizer_llm)

    return App(
        name="context_agent_app",
        root_agent=agent,
        plugins=[],
        events_compaction_config=EventsCompactionConfig(
            compaction_interval=5,
            overlap_size=2,
            summarizer=summarizer,
        ),
    )
