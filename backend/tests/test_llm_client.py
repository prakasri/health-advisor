"""AnthropicLLM error mapping (AI-001 §1, §5) with the SDK call stubbed — no network."""

from types import SimpleNamespace

import anthropic
import httpx2
import pytest

from app.llm import AnthropicLLM, LLMError, get_llm, set_llm
from app.safety.judge import JudgeVerdict

REQUEST = httpx2.Request("POST", "https://api.anthropic.com/v1/messages")


def client_returning(result):
    llm = AnthropicLLM(api_key="test", model_id="claude-sonnet-5")
    captured = {}

    def parse(**kwargs):
        captured.update(kwargs)
        if isinstance(result, Exception):
            raise result
        return result

    llm._client = SimpleNamespace(messages=SimpleNamespace(parse=parse))
    return llm, captured


def call(llm):
    return llm.generate(
        node="safety_check", system="sys", payload={"a": 1}, output=JudgeVerdict, effort="low"
    )


def test_success_returns_parsed_output_and_sends_expected_params():
    verdict = JudgeVerdict(passed=True, problems=[])
    llm, sent = client_returning(SimpleNamespace(stop_reason="end_turn", parsed_output=verdict))
    assert call(llm) is verdict
    assert sent["model"] == "claude-sonnet-5"
    assert sent["output_format"] is JudgeVerdict
    assert sent["output_config"] == {"effort": "low"}
    assert "temperature" not in sent  # rejected by Claude Sonnet 5
    assert sent["messages"] == [{"role": "user", "content": '{"a": 1}'}]


@pytest.mark.parametrize("stop_reason", ["refusal", "max_tokens"])
def test_refusal_and_truncation_raise(stop_reason):
    llm, _ = client_returning(SimpleNamespace(stop_reason=stop_reason, parsed_output=None))
    with pytest.raises(LLMError, match=stop_reason):
        call(llm)


def test_missing_parsed_output_raises():
    llm, _ = client_returning(SimpleNamespace(stop_reason="end_turn", parsed_output=None))
    with pytest.raises(LLMError, match="no structured output"):
        call(llm)


@pytest.mark.parametrize(
    "error",
    [
        anthropic.APIConnectionError(request=REQUEST),
        anthropic.RateLimitError(
            "slow down", response=httpx2.Response(429, request=REQUEST), body=None
        ),
        anthropic.InternalServerError(
            "oops", response=httpx2.Response(500, request=REQUEST), body=None
        ),
    ],
)
def test_api_errors_become_llm_errors(error):
    llm, _ = client_returning(error)
    with pytest.raises(LLMError):
        call(llm)


def test_get_llm_is_none_without_key_and_respects_override(monkeypatch):
    from app.config import settings

    monkeypatch.setattr(settings, "anthropic_api_key", "")
    assert get_llm() is None
    monkeypatch.setattr(settings, "anthropic_api_key", "sk-test")
    assert isinstance(get_llm(), AnthropicLLM)
    sentinel = SimpleNamespace(model_id="x")
    set_llm(sentinel)
    try:
        assert get_llm() is sentinel
    finally:
        set_llm(None)
