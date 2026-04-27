"""
Context Agent — A context-engineered AI agent built with Google ADK.

Uses Ollama (gemma4) locally, with long-term memory, conversation compaction,
and Langfuse observability.
"""

from .agent import agent

__all__ = ["agent"]
