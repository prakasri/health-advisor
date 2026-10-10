# Health Advisor — agent instructions

Specification-driven project. Specs in `specs/` are the source of truth; code implements them.

## Rules
- Read the relevant spec before changing code. If code and spec disagree, fix the spec first (PR), then the code.
- Reference spec / feature IDs in commit messages, e.g. `feat(F1.2): classify HbA1c per CLS-001`.
- Clinical logic (classification, BMI, calories, risk factors, monitoring) is deterministic Python that reads
  `specs/clinical/*.yaml`. Never move it into an LLM prompt.
- The LLM only writes diet, lifestyle and narrative text, via structured output validated by Pydantic.
- Never produce diagnostic or medication wording; see `specs/ai/guardrails-spec.md` and `banned-terms.yaml`.
- Never commit secrets. `.env` files are ignored; use `.env.example`.

## Layout
- `specs/` — specs; `00-build-plan.md` tracks phase status
- `backend/` — FastAPI + LangGraph (Python 3.12, uv). `uv run pytest`, `uv run ruff check .`
- `frontend/` — Next.js 16 + TypeScript (npm). Read `frontend/AGENTS.md` before writing frontend code.
- `deploy/` — Docker Compose + Caddy for the EC2 host

## Run locally
- API: `cd backend && uv run uvicorn app.main:app --reload` (port 8000)
- Phoenix: `cd backend && uv run phoenix serve` (UI on http://localhost:6006)
- Web: `cd frontend && npm run dev` (port 3001 — 3000 is used by another local project; `/api/*` proxied to port 8000)
