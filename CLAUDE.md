# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Context Agent is a locally-run AI assistant with persistent long-term memory, conversation compaction, and Langfuse observability. It uses **Google ADK** as the agent framework, **LiteLLM** to talk to a local **Ollama** instance (model: `gemma4`), and stores memories in `data/memories.json`.

## Running the Agent

```bash
uv run python main.py
```

Requires:

- Ollama running locally at `http://localhost:11434` with the `gemma4` model pulled
- `.env` file with `LANGFUSE_*` keys and `OLLAMA_API_BASE`

## In-session Commands

| Command       | Effect                                        |
| ------------- | --------------------------------------------- |
| `/quit`     | Save memories from this session and exit      |
| `/memories` | Print all stored facts from `memories.json` |
| `/clear`    | Delete all stored memories                    |
| `/debug`    | Dump raw ADK session events to console        |

## Architecture

### Data Flow

```
user input → Runner → App (compaction) → Agent → LiteLLM → Ollama
                                            ↕
                                       remember_fact / recall_memories (tools)
                                            ↕
                                      data/memories.json
```

### Key Components

| File                                | Role                                                                                                                         |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| `main.py`                         | Entry point — wires services, runs the chat loop                                                                            |
| `context_agent/agent.py`          | ADK `Agent` definition — model, system prompt, tools                                                                      |
| `context_agent/app.py`            | ADK `App` — wraps agent, configures `EventsCompactionConfig`                                                            |
| `context_agent/tools.py`          | `remember_fact` and `recall_memories` — read/write `memories.json`                                                    |
| `context_agent/memory_service.py` | `JsonFileMemoryService` (extends `BaseMemoryService`) — called at session end to auto-extract facts via heuristic regex |
| `context_agent/tracing.py`        | Langfuse + OpenTelemetry setup via `GoogleADKInstrumentor`                                                                 |

### Memory Architecture (Two Layers)

1. **During conversation** — the agent calls `remember_fact` / `recall_memories` tools directly, writing/reading `data/memories.json` immediately.
2. **At session end** (`/quit` or Ctrl-C) — `JsonFileMemoryService.add_session_to_memory()` runs a heuristic regex pass over the full conversation to catch anything the agent missed.

### Conversation Compaction

Configured in `app.py` via `EventsCompactionConfig`:

- Every 5 completed turns, older events are summarized by the same Ollama model.
- 2 turns of overlap are kept for continuity.
- This keeps the context window lean for long sessions.

### Ollama KV Caching

Ollama automatically caches the prompt prefix in VRAM as long as the model stays loaded (default 5 min). The stable system instruction in `agent.py` is intentionally placed first to maximize prefix cache hits. `keep_alive=-1` keeps the model loaded indefinitely.

### Tracing

`setup_tracing()` in `tracing.py` must be called **before** any ADK imports. It registers `GoogleADKInstrumentor` (OpenTelemetry) and ships spans to Langfuse. LiteLLM's own callbacks are explicitly cleared to prevent conflicting telemetry.

## Environment Variables (`.env`)

```


LANGFUSE_SECRET_KEY=...
LANGFUSE_PUBLIC_KEY=...
LANGFUSE_BASE_URL=https://us.cloud.langfuse.com

OLLAMA_API_KEY=ollama
OLLAMA_API_BASE=http://localhost:11434
```
