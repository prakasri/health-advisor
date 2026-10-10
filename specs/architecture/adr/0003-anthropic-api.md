# ADR 0003 — Anthropic API directly (not Amazon Bedrock) for the MVP

- Status: accepted · Date: 2026-10-10

## Context
Bedrock keeps traffic in AWS but needs model-access setup per region; the Anthropic API needs only a key.

## Decision
Use the Anthropic API via `langchain-anthropic`, model `claude-sonnet-5` (configurable). The model
factory is isolated in `app/graph/llm.py` so switching to `ChatBedrockConverse` is a one-file change.

## Consequences
+ Fastest setup. − Inputs leave AWS to Anthropic (no identifiers are sent). Revisit in V2 (Bedrock).
