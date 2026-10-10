"""Phoenix tracing (AI-001 §7). LangGraph node spans via the LangChain instrumentor (LangGraph
runs on langchain-core callbacks); model calls via the Anthropic instrumentor."""

from contextlib import AbstractContextManager, nullcontext

from opentelemetry import trace

from app.config import settings

_tracer: trace.Tracer | None = None
_provider = None


def setup_tracing() -> None:
    global _tracer, _provider
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
    _provider = provider


def assessment_span(attributes: dict) -> AbstractContextManager:
    """Root span for one graph run; attributes are set again at the end via set_attributes."""
    if _tracer is None:
        return nullcontext(None)
    return _tracer.start_as_current_span(
        "assessment", attributes={"openinference.span.kind": "CHAIN", **attributes}
    )


def flush(timeout_ms: int = 5000) -> None:
    """Export buffered spans now, inside the request.

    Cloud Run throttles CPU once a response is sent, so the background batch exporter may never run
    for a long request; flushing before returning makes every assessment trace reach Phoenix."""
    if _provider is not None:
        _provider.force_flush(timeout_ms)
