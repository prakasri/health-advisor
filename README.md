# Health Advisor — Diabetes Assessment Platform

Enter an HbA1c result and a short health profile; get a personalised, evidence-based report: where
the result falls, a food plan that fits your diet and cuisine, an activity plan, the tests and
screenings to ask about, and questions for your doctor — as a web page, a PDF and a shareable link.

Built with **Specification-Driven Development** as an academic project.

> Educational and wellness guidance only. It is not a medical diagnosis, never advises on medication,
> and does not replace a qualified healthcare professional.

## Results at a glance

| | |
| --- | --- |
| Acceptance criteria (PRD-001) | 10 / 10 met locally — [evidence](specs/quality/acceptance-evidence.md) |
| Live AI evaluation (16 golden cases, `claude-sonnet-5`) | 0 unsafe reports shown · 100% delivered without fallback · 94% first-attempt safety pass · p95 25.2 s — [results](specs/quality/eval-results/2026-10-10T1142Z.md) |
| Automated tests | 267 backend tests (incl. the Gherkin acceptance specs) · 97% coverage · frontend type-check, lint and build |
| Accessibility | 14 / 15 WCAG 2.2 AA checks pass — [checklist](specs/quality/accessibility-checklist.md) |
| Build phases | 0–4, 6, 7 done; 9 done locally; 5 and 8 (deploy to Vercel + AWS) pending — [build plan](specs/00-build-plan.md) |

## How it works

```
Browser ──> Next.js 16 (Vercel) ── /api/* rewrite ──> FastAPI (AWS EC2) ──> PostgreSQL (RDS)
                                                          │
                                       LangGraph assessment graph
                    rules first ─────────────────────────┴──────────── then AI
   eligibility · HbA1c class · urgent flag ·     diet ‖ lifestyle ‖ narrative writers (Claude)
   BMI · calories · risk factors · monitoring     → safety check (rules + LLM judge)
   (deterministic, from specs/clinical/*.yaml)    → 1 retry with feedback → safe fallback text
                                                          │
                                         traces ──> Arize Phoenix
```

- **Rules for facts, AI for personalisation** ([ADR 0001](specs/architecture/adr/0001-rules-vs-llm.md)):
  classification, BMI, calorie target, risk factors and monitoring are Python reading versioned YAML;
  the model only writes the diet, lifestyle and summary text, from those facts.
- **Safety layers** ([GR-001](specs/ai/guardrails-spec.md)): ineligible users (under 18, pregnant,
  type 1) get a referral with no AI call; AI output is checked for diagnostic or medication language,
  diet-preference violations, wrong numbers and comorbidity conflicts, then by an LLM judge; anything
  failing twice falls back to safe standard text.
- **No accounts, no identity** ([ADR 0002](specs/architecture/adr/0002-no-accounts.md)): share links
  are 256-bit tokens that expire in 30 days and can be revoked; data is deleted after 90 days.

## Specification-driven development

Specs come first and are the source of truth — code reads them or is generated from them.

| Where | What |
| --- | --- |
| [`specs/00-index.md`](specs/00-index.md) | Spec index and **traceability matrix** (requirement → spec → acceptance → code → tests) |
| [`specs/00-build-plan.md`](specs/00-build-plan.md) | Phase plan and status |
| `specs/product/` | Vision, PRD, user journeys |
| `specs/functional/` | Feature specs F1–F5 and **executable Gherkin acceptance criteria** |
| `specs/clinical/` | Clinical rules (YAML) and [references](specs/clinical/references.md) (ADA Standards of Care 2026) |
| `specs/ai/` | LangGraph spec, versioned prompts, guardrails, banned terms, fallback text, evaluation spec |
| `specs/data/schemas/` | JSON Schemas → generated Pydantic models (`backend/app/schemas/`) and TypeScript types |
| `specs/architecture/` | Architecture, OpenAPI contract, deployment, ADRs 0001–0004 |
| `specs/quality/` | Test strategy, golden cases + oracle, eval results, accessibility, acceptance evidence, [demo script](specs/quality/demo-script.md) |

## Stack
Next.js 16 + TypeScript + Tailwind (Vercel) · Python 3.12, FastAPI, LangGraph, Anthropic SDK
(Claude Sonnet 5) · PostgreSQL 16 + Alembic · WeasyPrint (PDF) · Arize Phoenix · AWS ap-south-1
(EC2, RDS, SSM) · GitHub Actions

## Run it locally

Prerequisites: Python 3.12 + [uv](https://docs.astral.sh/uv/), Node 20+, PostgreSQL 16+, and on
macOS `brew install pango` for PDFs (the API finds Homebrew's libraries automatically).

```bash
# 1. database (once)
createuser -P health_advisor        # password: health_advisor (local only)
createdb -O health_advisor health_advisor

# 2. backend (terminal 1)
cd backend && cp .env.example .env  # add ANTHROPIC_API_KEY for AI reports (optional)
uv sync && uv run alembic upgrade head
uv run uvicorn app.main:app --reload          # http://localhost:8000/docs

# 3. tracing (terminal 2)
cd backend && uv run phoenix serve            # http://localhost:6006

# 4. frontend (terminal 3)
cd frontend && cp .env.example .env.local && npm install
npm run dev                                   # http://localhost:3001
```

Without an API key the app still works end to end: reports use the safe standard text instead of AI.
Port in use? `lsof -nP -iTCP:3001 -sTCP:LISTEN` shows what holds it.

## Tests and evaluation

```bash
cd backend
uv run pytest -q --cov=app          # unit, golden, graph (fake LLM), API, PDF/share, Gherkin acceptance
uv run ruff check .
uv run python -m evals.run_golden   # live evaluation on the 16 golden cases (needs API key; ~$1–3)

cd ../frontend
npm run typecheck && npm run lint && npx next build
```

CI ([`.github/workflows/ci.yml`](.github/workflows/ci.yml)) runs all of the above except the live
evaluation, and fails if generated schemas or API types drift from the specs.

## Repository layout
```
specs/      specifications (source of truth)
backend/    FastAPI + LangGraph + rules engine + PDF (Python, uv)
frontend/   Next.js app (TypeScript, npm)
deploy/     Docker Compose + Caddy for the EC2 host
```
