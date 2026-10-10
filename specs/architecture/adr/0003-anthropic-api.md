# ADR 0003 — Anthropic API directly (not Amazon Bedrock) for the MVP

- Status: accepted · Date: 2026-10-10

## Context
Bedrock keeps traffic in AWS but needs model-access setup per region; the Anthropic API needs only a key.

## Decision
Use the Anthropic API through the official `anthropic` Python SDK (`messages.parse` with Pydantic
structured output), model `claude-sonnet-5` (configurable). LangGraph nodes call the SDK through a
small client in `app/graph/llm.py`, so switching to Bedrock (`AnthropicBedrockMantle`) is a one-file
change. Claude Sonnet 5 rejects `temperature`; output variety is controlled by the prompt and
`output_config.effort`. Phoenix traces the SDK calls via `openinference-instrumentation-anthropic`.

## Consequences
+ Fastest setup. − Inputs leave AWS to Anthropic (no identifiers are sent). Revisit in V2 (Bedrock).
