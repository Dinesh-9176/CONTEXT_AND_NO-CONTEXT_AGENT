"""
Langfuse + OpenTelemetry tracing setup for the context agent.

Uses GoogleADKInstrumentor to auto-instrument all ADK calls and send
OTel spans to Langfuse. Must be called BEFORE any ADK imports.
"""

import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def setup_tracing(variant: str = "with_context_engineering"):
    """
    Initialize Langfuse client and instrument ADK with OpenTelemetry.

    Must be called BEFORE creating any agent or runner instances.

    Args:
        variant: Sets the OTel service name — makes CE vs. no-CE traces
                 easy to separate in Langfuse (filter by service.name).

    Returns:
        The Langfuse client instance (call .flush() on exit).
    """
    os.environ.setdefault("OTEL_SERVICE_NAME", variant)

    from openinference.instrumentation.google_adk import GoogleADKInstrumentor
    from langfuse import get_client

    langfuse = get_client()

    if langfuse.auth_check():
        print("[OK] Langfuse connected successfully")
    else:
        print("[WARN] Langfuse authentication failed - traces won't be sent")
        print("  Check LANGFUSE_PUBLIC_KEY, LANGFUSE_SECRET_KEY, LANGFUSE_BASE_URL in .env")

    GoogleADKInstrumentor().instrument()
    print("[OK] ADK OpenTelemetry instrumentation active")

    # Disable LiteLLM's own callbacks and async logging worker —
    # OTel already captures everything, and the worker throws TimeoutErrors
    # when it can't reach external telemetry endpoints.
    try:
        import logging
        import litellm
        litellm.success_callback = []
        litellm.failure_callback = []
        litellm._async_success_callback = []
        litellm._async_failure_callback = []
        litellm.callbacks = []
        litellm._turn_off_scanned_callbacks = True
        litellm.telemetry = False
        # Silence the async worker's error logs — they're noise, not failures
        logging.getLogger("LiteLLM").setLevel(logging.CRITICAL)
    except ImportError:
        pass

    return langfuse
