"""
Langfuse + OpenTelemetry tracing — identical pipeline to context_agent,
tagged without_context_engineering for comparison in Langfuse.
"""

import os
import sys

if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stderr.reconfigure(encoding="utf-8", errors="replace")


def setup_tracing(variant: str = "without_context_engineering"):
    """
    Initialize Langfuse and instrument ADK with OpenTelemetry.
    Must be called BEFORE creating any agent or runner instances.
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
        logging.getLogger("litellm").setLevel(logging.CRITICAL)
    except ImportError:
        pass

    return langfuse
