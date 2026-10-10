# Health Advisor — Diabetes Assessment Platform

Educational web app: enter an HbA1c value and health profile, get a classified, personalised
lifestyle, diet and monitoring report (PDF + share link). Built with Specification-Driven
Development as an academic project.

> Educational and wellness guidance only. Not a medical diagnosis; does not replace a doctor.

## Stack
Next.js + TypeScript (Vercel) · FastAPI + LangGraph (Python 3.12) · PostgreSQL · AWS (EC2, RDS, SSM, ap-south-1) · Arize Phoenix

## Specs
Start at [`specs/00-build-plan.md`](specs/00-build-plan.md). All specs live in `specs/`.

## Local development

Prerequisites: Python 3.12 + [uv](https://docs.astral.sh/uv/), Node 20+, PostgreSQL 16+,
and for PDF rendering on macOS: `brew install pango`.

```bash
# database (once)
createuser -P health_advisor        # password: health_advisor (local only)
createdb -O health_advisor health_advisor

# backend
cd backend && cp .env.example .env && uv sync
uv run uvicorn app.main:app --reload          # http://localhost:8000/api/health

# tracing (separate terminal)
cd backend && uv run phoenix serve            # http://localhost:6006

# frontend (separate terminal)
cd frontend && cp .env.example .env.local && npm install
npm run dev                                   # http://localhost:3001
```

## Tests
```bash
cd backend && uv run pytest && uv run ruff check .
cd frontend && npm run lint
```
