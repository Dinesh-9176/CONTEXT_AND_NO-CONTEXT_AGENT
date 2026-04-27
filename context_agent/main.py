"""
Context Agent — Interactive CLI (WITH Context Engineering)

Features:
- Local Ollama (gemma4) via Google ADK + LiteLLM
- Long-term memory (JSON-file backed)
- Conversation compaction (EventsCompactionConfig)
- Ollama implicit KV caching
- Langfuse observability (OpenTelemetry)
"""

import asyncio
import os
import re
import sys
import uuid

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv


async def main():
    load_dotenv()

    print("\n" + "=" * 60)
    print("  Context Agent  [WITH Context Engineering]")
    print("  ADK + Ollama + Langfuse")
    print("=" * 60)

    from context_agent.tracing import setup_tracing
    langfuse = setup_tracing(variant="with_context_engineering")

    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    from context_agent.app import create_app
    from context_agent.memory_service import JsonFileMemoryService

    session_service = InMemorySessionService()
    memory_service = JsonFileMemoryService()

    APP_NAME = "context_agent_app"
    USER_ID = "default_user"
    SESSION_ID = f"with_ce_{uuid.uuid4()}"

    await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID,
    )

    app = create_app()
    runner = Runner(
        app=app,
        session_service=session_service,
        memory_service=memory_service,
    )

    print(f"\n  Session : {SESSION_ID}")
    print(f"  Model   : ollama_chat/gemma4")
    print(f"  Traces  : Langfuse ({os.getenv('LANGFUSE_BASE_URL', 'N/A')})")
    print(f"  Memory  : data/memories.json")
    print(f"  Compact : every 5 turns (overlap 2)")
    print("\nCommands: /quit  /memories  /clear  /debug")
    print("-" * 60 + "\n")

    try:
        while True:
            try:
                user_input = input("You: ").strip()
            except EOFError:
                break

            if not user_input:
                continue

            if user_input.lower() == "/quit":
                print("\n[SAVING] Extracting memories from this session...")
                session = await session_service.get_session(
                    app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID,
                )
                if session:
                    await memory_service.add_session_to_memory(session)
                print("[OK] Memories saved. Goodbye!\n")
                break

            if user_input.lower() == "/memories":
                memories = memory_service._load()
                if not memories:
                    print("\n[EMPTY] No memories stored yet.\n")
                else:
                    print(f"\n[MEMORY] Stored Memories ({len(memories)}):")
                    for i, mem in enumerate(memories, 1):
                        print(f"  {i}. {mem['fact']}  ({mem.get('source', 'unknown')})")
                    print()
                continue

            if user_input.lower() == "/clear":
                memory_service._save([])
                print("\n[CLEARED] All memories cleared.\n")
                continue

            if user_input.lower() == "/debug":
                print("\n[DEBUG] Fetching raw session state...")
                session = await session_service.get_session(
                    app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID,
                )
                if not session:
                    print("  No session found.")
                else:
                    events = session.events
                    print(f"  Total Events: {len(events)}")
                    for i, evt in enumerate(events):
                        print(f"\n  --- Event {i+1} ({type(evt).__name__}) ---")
                        if hasattr(evt, 'summary') and evt.summary:
                            print(f"  [COMPACTED SUMMARY]: {evt.summary}")
                        elif hasattr(evt, 'content') and evt.content:
                            for part in evt.content.parts:
                                if part.text: print(f"  Text: {part.text[:200]}...")
                                if part.function_call: print(f"  Tool Call: {part.function_call.name}")
                                if part.function_response: print(f"  Tool Result: {part.function_response.name}")
                        else:
                            print(f"  Raw: {evt}")
                print()
                continue

            user_msg = types.Content(role="user", parts=[types.Part(text=user_input)])
            print("Agent: ", end="", flush=True)

            response_text = ""
            async for event in runner.run_async(
                user_id=USER_ID, session_id=SESSION_ID, new_message=user_msg,
            ):
                if event.is_final_response():
                    if event.content and event.content.parts:
                        for part in event.content.parts:
                            if part.text:
                                response_text += part.text

            print(_clean(response_text) if response_text else "(no response)")
            print()

    except KeyboardInterrupt:
        print("\n\n[INTERRUPT] Saving memories...")
        session = await session_service.get_session(
            app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID,
        )
        if session:
            await memory_service.add_session_to_memory(session)
        print("[OK] Memories saved. Goodbye!\n")

    finally:
        if langfuse:
            langfuse.flush()
            print("[OK] Langfuse traces flushed.")


def _clean(text: str) -> str:
    """Strip <think>...</think> blocks that some Ollama thinking models emit."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


if __name__ == "__main__":
    asyncio.run(main())
