"""
Benchmark — WITH Context Engineering

Sends 15 fixed prompts, records per-turn latency, prints p50/p90/p95.
Traces land in Langfuse under service.name=with_context_engineering.
Filter sessions by prefix: bench_with_ce_

Usage:
    uv run python benchmark.py
"""

import asyncio
import sys
import time
import uuid

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")

from dotenv import load_dotenv

BENCHMARK_PROMPTS = [
    "Hi, my name is Alex and I work as a data engineer.",
    "I'm currently building a real-time pipeline using Apache Kafka.",
    "What is 17 multiplied by 6?",
    "Tell me a short joke.",
    "What are common serialization formats used in data pipelines?",
    "My favorite programming language is Python.",
    "I also like using dbt for transformations.",
    "What do you remember about me so far?",
    "I enjoy hiking and photography on weekends.",
    "Give me a brief summary of everything you know about me.",
    "What is the capital of Japan?",
    "What is the difference between a list and a tuple in Python?",
    "I recently moved to Bangalore.",
    "What frameworks would you recommend for my Kafka project?",
    "Thanks for the chat!",
]


async def run_benchmark():
    load_dotenv()

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
    USER_ID = "benchmark_user"
    SESSION_ID = f"bench_with_ce_{uuid.uuid4()}"

    await session_service.create_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID,
    )

    app = create_app()
    runner = Runner(app=app, session_service=session_service, memory_service=memory_service)

    print("\n" + "=" * 60)
    print("  BENCHMARK — With Context Engineering")
    print(f"  Session : {SESSION_ID}")
    print(f"  Prompts : {len(BENCHMARK_PROMPTS)}")
    print("=" * 60)

    latencies: list[float] = []

    for i, prompt in enumerate(BENCHMARK_PROMPTS, 1):
        user_msg = types.Content(role="user", parts=[types.Part(text=prompt)])
        start = time.perf_counter()
        async for event in runner.run_async(
            user_id=USER_ID, session_id=SESSION_ID, new_message=user_msg,
        ):
            if event.is_final_response():
                pass
        elapsed = time.perf_counter() - start
        latencies.append(elapsed)
        print(f"  [{i:02d}/{len(BENCHMARK_PROMPTS)}] {elapsed:.2f}s  {prompt[:55]!r}")

    session = await session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID,
    )
    if session:
        await memory_service.add_session_to_memory(session)

    _print_summary(latencies, "With Context Engineering", "bench_with_ce_")

    if langfuse:
        langfuse.flush()


def _print_summary(latencies: list[float], label: str, prefix: str) -> None:
    if not latencies:
        return
    s = sorted(latencies)
    n = len(s)
    print("\n" + "=" * 60)
    print(f"  RESULTS — {label}")
    print("=" * 60)
    print(f"  Turns   : {n}")
    print(f"  Total   : {sum(latencies):.2f}s")
    print(f"  Average : {sum(latencies)/n:.2f}s")
    print(f"  P50     : {s[int(n*0.50)]:.2f}s")
    print(f"  P90     : {s[min(int(n*0.90), n-1)]:.2f}s")
    print(f"  P95     : {s[min(int(n*0.95), n-1)]:.2f}s")
    print(f"  Min/Max : {min(latencies):.2f}s / {max(latencies):.2f}s")
    print("=" * 60)
    print(f"  Langfuse filter  → service.name = with_context_engineering")
    print(f"  Session prefix   → {prefix}")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(run_benchmark())
