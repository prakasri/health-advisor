---
id: PLAN-001
title: Phase-wise build plan
status: approved
version: 1.0
depends_on: [VIS-001, PRD-001]
last_reviewed: 2026-10-10
---

# Build plan — 2 days, solo

Blueprint: Diabetes Assessment Platform — 2-Day SDD Blueprint (Claude Docs).
Hosting decision: frontend on Vercel, backend on AWS `ap-south-1` (see ADR 0004).

Every phase ends with an exit check. Do not start the next phase until it passes.

## Day 1 — specs, engine, AI (~8.5 h)

| Phase | Time | Work | Exit check |
| --- | --- | --- | --- |
| 0. Setup | 0.5 h | Repo scaffold, uv backend, Next.js frontend, local Postgres + Phoenix, `.env.example`, gitleaks pre-commit, Vercel project linked | Backend and frontend start locally; Phoenix UI on :6006 |
| 1. Core specs | 2.5 h | JSON schemas → clinical rule YAMLs → guardrails + banned terms → LangGraph spec + prompts → OpenAPI + data model → vision, PRD, journeys, F1–F5, Gherkin, eval spec + 20 golden cases, test strategy | All specs have front-matter; schemas validate; monitoring rules verified against ADA Standards of Care |
| 2. Rules engine | 1.5 h | `classify`, `metrics`, `risk`, `monitoring` reading YAML; boundary tests | 100% rule tests green; 20/20 golden cases match on rule outputs |
| 3. API + DB | 1 h | Alembic migrations (4 tables), Pydantic models, `/classify`, `/assessments` (LLM stubbed), `/reports/{id}`, `/health` | Contract tests pass against `openapi.yaml` |
| 4. LangGraph + LLM | 2.5 h | 11-node graph, parallel writers, safety check, retry + fallback, structured output, Phoenix tracing | Golden cases run end to end; safety pass ≥ 95%; ineligible = 0 LLM spans; p95 < 30 s |
| 5. Skeleton deploy | 0.5 h | EC2 + Docker Compose + Caddy, RDS, SSM; Vercel with `/api` rewrite | Public `/api/health` returns 200 through Vercel |

## Day 2 — product, output, ship (~7 h)

| Phase | Time | Work | Exit check |
| --- | --- | --- | --- |
| 6. Frontend | 3.5 h | Landing + disclaimer, 3-step form, instant classification, progress, report page, urgent banner, a11y basics | Meena, Priya, Joseph journeys work in the browser |
| 7. PDF + share + feedback | 1 h | WeasyPrint template, share create/view/revoke, feedback | PDF < 5 s; revoked link → 404 |
| 8. Production deploy + hardening | 1.5 h | Rate limit, Phoenix basic auth, security groups, retention job, preview → staging API | Smoke test on live URL; production traces in Phoenix |
| 9. Evidence + submission | 1 h | Acceptance suite, traceability matrix, README, screenshots, demo video | All MVP acceptance criteria ticked |

## Descope order (if behind)

1. Feedback endpoint
2. Share-link revocation
3. LLM-judge part of `safety_check` (keep rule checks)
4. Extra regional cuisines
5. Last resort: serve Next.js from the EC2 instead of Vercel

## Status

| Phase | Status | Notes |
| --- | --- | --- |
| 0 | done (2 items open) | API, web (port 3001) and Phoenix verified locally; `/api` rewrite works. No local Docker: local Postgres 17 + `arize-phoenix` via uv; Docker only on EC2. Open: create local `health_advisor` DB (needs Postgres password); Vercel link moved to Phase 5 |
| 1–9 | not started | Anthropic API key needed before Phase 4 |
