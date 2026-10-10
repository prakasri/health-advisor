---
id: ARC-001
title: Architecture
status: approved
version: 1.0.0
depends_on: [PRD-001, AI-001, DM-001]
last_reviewed: 2026-10-10
---

# ARC-001 Architecture

Three tiers: Next.js frontend (Vercel) → FastAPI + LangGraph (EC2) → PostgreSQL (RDS). Phoenix
receives traces. The API contract is `openapi.yaml`; deployment is `deployment.md`.

```
Browser ──HTTPS──> Vercel (Next.js 16)
                     │  /api/* rewrite (ADR 0004)
                     ▼
              Caddy (TLS) on EC2 ──> FastAPI ──> LangGraph assessment_graph
                                        │              │
                                        │              ├─ rules (app/rules, reads specs/clinical/*.yaml)
                                        │              └─ LLM nodes ──HTTPS──> Anthropic API (Claude Sonnet 5)
                                        ├─ WeasyPrint (PDF)
                                        ├─ OTLP traces ──> Phoenix (EC2) ──> RDS "phoenix" DB
                                        └─ SQLAlchemy ──> RDS PostgreSQL "health_advisor" DB
```

## Backend modules (`backend/app/`)

| Module | Responsibility | Depends on |
| --- | --- | --- |
| `config.py` | Settings from env | — |
| `schemas.py` | Pydantic models generated from `specs/data/schemas` | — |
| `rules/` | `loader.py` (YAML), `eligibility.py`, `classify.py`, `metrics.py`, `risk.py`, `monitoring.py` | schemas, specs/clinical |
| `llm/` | `client.py` (Anthropic SDK client behind an `LLMClient` protocol; `set_llm` for tests), `prompts.py` | specs/ai/prompts |
| `safety/` | `checks.py` (S1–S6), `judge.py` (J1), `fallback.py` | schemas, llm, specs/ai |
| `graph/` | `state.py`, `nodes.py`, `graph.py` | rules, safety, llm, report |
| `assessment.py` | Runs the graph inside a root trace span → `AssessmentOutcome` | graph |
| `report/` | `assemble.py` (state → Report), `pdf.py`, `templates/report.html` | schemas |
| `db/` | `models.py`, `session.py`, `repository.py`, Alembic migrations | — |
| `api/` | `routes.py` (all endpoints), `ratelimit.py` | graph, report, db |
| `tracing.py` | Phoenix registration | — |
| `main.py` | App factory, start-up (load specs, compile graph, tracing) | all |

Dependency rule: `rules`, `llm` and `safety` never import `graph`, `api` or `db`.

## Frontend (`frontend/app/`)

| Route | Purpose |
| --- | --- |
| `/` | Landing + disclaimer acknowledgement |
| `/assess/step-1`, `/assess/step-2`, `/assess/step-3` | Form steps (client components, sessionStorage) |
| `/assess/referral` | Ineligible exit |
| `/report/[id]` | Report view, PDF, share, feedback |
| `/share/[token]` | Read-only shared report (`noindex`) |

Types: `frontend/lib/api-types.ts` generated from `openapi.yaml` (openapi-typescript).

## Key decisions
ADR 0001 rules vs LLM · ADR 0002 no accounts · ADR 0003 Anthropic API for MVP · ADR 0004 Vercel frontend.
