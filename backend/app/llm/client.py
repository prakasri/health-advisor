"""LLM access for graph nodes (AI-001 §1, ADR 0003). Nodes depend on the LLMClient protocol so
tests can inject a fake and Bedrock can replace the Anthropic API in one place."""

import json
from typing import Protocol, TypeVar

import anthropic
from pydantic import BaseModel

from app.config import settings

T = TypeVar("T", bound=BaseModel)


class LLMError(Exception):
    """The model did not return a usable structured output (refusal, truncation, API error)."""


class LLMClient(Protocol):
    model_id: str

    def generate(
        self, *, node: str, system: str, payload: dict, output: type[T], effort: str
    ) -> T: ...


class AnthropicLLM:
    def __init__(self, api_key: str, model_id: str, workspace_id: str | None = None) -> None:
        self.model_id = model_id
        headers = {"anthropic-workspace-id": workspace_id} if workspace_id else None
        self._client = anthropic.Anthropic(
            api_key=api_key, timeout=settings.llm_timeout_s, max_retries=2, default_headers=headers
        )

    def generate(self, *, node: str, system: str, payload: dict, output: type[T], effort: str) -> T:
        try:
            response = self._client.messages.parse(
                model=self.model_id,
                max_tokens=settings.llm_max_tokens,
                system=system,
                messages=[{"role": "user", "content": json.dumps(payload, ensure_ascii=False)}],
                output_format=output,
                output_config={"effort": effort},
            )
        except anthropic.APIConnectionError as exc:
            raise LLMError(f"{node}: connection failed") from exc
        except anthropic.RateLimitError as exc:
            raise LLMError(f"{node}: rate limited") from exc
        except anthropic.APIStatusError as exc:
            raise LLMError(f"{node}: API error {exc.status_code}: {exc.message}") from exc

        if response.stop_reason in ("refusal", "max_tokens"):
            raise LLMError(f"{node}: stopped with {response.stop_reason}")
        if response.parsed_output is None:
            raise LLMError(f"{node}: no structured output")
        return response.parsed_output


_override: LLMClient | None = None


def set_llm(client: LLMClient | None) -> None:
    """Tests inject a fake here; pass None to restore the default."""
    global _override
    _override = client


def get_llm() -> LLMClient | None:
    """The active client, or None when no API key is configured (graph then uses fallback text)."""
    if _override is not None:
        return _override
    if not settings.anthropic_api_key:
        return None
    return AnthropicLLM(
        settings.anthropic_api_key, settings.llm_model, settings.anthropic_workspace_id
    )
