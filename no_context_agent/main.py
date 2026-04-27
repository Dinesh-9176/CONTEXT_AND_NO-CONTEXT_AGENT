"""
No-CE Agent — Interactive CLI (WITHOUT Context Engineering)

No memory, no compaction, no tools. Pure stateless chat.
Langfuse tracing active for latency comparison.
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
    print("  No-CE Agent  [WITHOUT Context Engineering]")
    print("  ADK + Ollama + Langfuse")
    print("=" * 60)

    from no_context_agent.tracing import setup_tracing
    langfuse = setup_tracing(variant="without_context_engineering")

    from google.adk.apps.app import App
    from google.adk.runners import Runner
    from google.adk.sessions import InMemorySessionService
    from google.genai import types

    from no_context_agent.agent import agent

    session_service = InMemorySessionService()

    APP_NAME = "no_ce_agent_app"
    USER_ID = "default_user"
    SESSION_ID = f"no_ce_{uuid.uuid4()}"

    await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID,
    )

    app = App(name=APP_NAME, root_agent=agent)
    runner = Runner(app=app, session_service=session_service)

    print(f"\n  Session : {SESSION_ID}")
    print(f"  Model   : ollama_chat/gemma4")
    print(f"  Traces  : Langfuse ({os.getenv('LANGFUSE_BASE_URL', 'N/A')})")
    print(f"  Memory  : NONE")
    print(f"  Compact : NONE")
    print("\nCommands: /quit")
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
                print("\n[BYE] Goodbye!\n")
                break

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
        print("\n\n[INTERRUPT] Goodbye!\n")

    finally:
        if langfuse:
            langfuse.flush()
            print("[OK] Langfuse traces flushed.")


def _clean(text: str) -> str:
    """Strip <think>...</think> blocks that some Ollama thinking models emit."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


if __name__ == "__main__":
    asyncio.run(main())
