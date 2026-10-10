"""Phoenix tracing (AI-001 §7). LangGraph node spans via the LangChain instrumentor (LangGraph
runs on langchain-core callbacks); model calls via the Anthropic instrumentor."""

from contextlib import AbstractContextManager, nullcontext

from opentelemetry import trace

from app.config import settings

_tracer: trace.Tracer | None = None


def setup_tracing() -> None:
    global _tracer
    if not settings.tracing_enabled or _tracer is not None:
        return
    from openinference.instrumentation.anthropic import AnthropicInstrumentor
    from openinference.instrumentation.langchain import LangChainInstrumentor
    from phoenix.otel import register

    provider = register(
        project_name=settings.phoenix_project,
        endpoint=settings.phoenix_collector_endpoint,
        api_key=settings.phoenix_api_key or None,
        batch=True,
        verbose=False,
    )
    LangChainInstrumentor().instrument(tracer_provider=provider)
    AnthropicInstrumentor().instrument(tracer_provider=provider)
    _tracer = provider.get_tracer("health-advisor")


def assessment_span(attributes: dict) -> AbstractContextManager:
    """Root span for one graph run; attributes are set again at the end via set_attributes."""
    if _tracer is None:
        return nullcontext(None)
    return _tracer.start_as_current_span(
        "assessment", attributes={"openinference.span.kind": "CHAIN", **attributes}
    )
