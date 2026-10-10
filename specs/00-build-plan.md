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
| 1 | done (1 item open) | 12 core specs + 4 ADRs + index/traceability. Schemas, YAML, 20 golden inputs validated; banned patterns tested. ADA 2026 check done 2026-10-10: 9 monitoring items confirmed via secondary sources, eye/liver/lipid frequencies corrected; remaining items marked to verify / judgement in `clinical/references.md` |
| 2 | done | Rules engine in `backend/app/rules/` reading the YAML specs; Pydantic models generated from schemas (`scripts/gen_schemas.sh`). 75 tests pass, 20/20 golden cases exact, rules coverage 99% |
| 3 | done | Alembic migration (4 tables, `alembic check` clean); `/health`, `/classify`, `/assessments`, `/reports/{id}`; reports built from rules + fallback text until Phase 4; spec-level validation (`none` exclusive); rate limit. 115 tests, coverage 98%; contract test fails if any `openapi.yaml` path is neither built nor scheduled |
| 4 | done | 11-node LangGraph graph, three parallel writers, safety checks S1–S6 + LLM judge, retry with feedback, rule-only fallback; official `anthropic` SDK with Pydantic structured output. Live EV-001 Tier 3 (2026-10-10T1142Z, 16 cases): 0 unsafe reports, 100% AI reports, 94% first-pass, p95 25.2 s, median 19.2 s — all targets met. Judge caught 1 real constraint miss (G08 alcohol), fixed on retry. 217 tests |
| 6 | done | Next.js 16 frontend: landing + acknowledgement, 3 form steps (instant classification, urgent banner, exclusive 'none', live BMI with Asian cut-offs), progress screen, referral exit, server-rendered 10-section report. Browser journeys passed 2026-10-10: Meena (full AI report), Priya (referral, no AI call), Joseph (urgent + kidney). Fixes from journeys: matched-only risk indicators (monitoring-rules 1.1.0), HbA1c one decimal, report opens at top, fallback text casing/list splitting, Start disabled until hydrated |
| 7 | done | PDF (WeasyPrint, A4, 10 sections, urgent first; warm-up at start-up: first PDF 0.28 s vs 4.8 s cold), share links (256-bit token, 30-day expiry, revoke, view count, same 404 for unknown/expired/revoked), feedback (yes/no + 500-char comment). Frontend: Download PDF, create/copy/stop sharing, feedback form, read-only `/share/[token]` page (noindex). 234 backend tests; browser-checked share → open → revoke → 404 and feedback |
| 9 | done locally (2 items need deploy) | Gherkin specs executable (33 scenarios, mutation-checked); accessibility Q-08 14/15 (focus-to-first-error added); AC-1–AC-10 evidence; README, demo script, CI workflow; specs approved. 267 tests, 97% coverage. Pending deploy: live smoke test, production traces; demo video is the student's to record |
| 5, 8 | not started | Needs AWS + Vercel account confirmation |
