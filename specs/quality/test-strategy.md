---
id: TS-001
title: Test strategy
status: approved
version: 1.0.0
depends_on: [PRD-001, EV-001]
last_reviewed: 2026-10-10
---

# TS-001 Test strategy

## Pyramid

| Layer | Tool | Scope | LLM | Runs |
| --- | --- | --- | --- | --- |
| Unit — rules | pytest | Each rule function; boundaries; YAML loading | none | every commit |
| Golden rules | pytest (`test_golden_rules.py`) | 20 cases, exact match (EV-001 Tier 1) | none | every commit |
| Safety checks | pytest | S1–S5 with crafted good/bad outputs; fallback content passes its own checks | none | every commit |
| Graph | pytest | Routing, parallel writers, retry, fallback, 0 LLM calls when ineligible (EV-001 Tier 2) | fake model | every commit |
| API contract | pytest + httpx TestClient | Every path in `openapi.yaml`, status codes, schema-valid bodies | fake model | every commit |
| Acceptance | pytest-bdd over `specs/functional/acceptance/*.feature` (`tests/bdd/test_acceptance.py`) | AC-1 – AC-8 (33 scenarios) | fake model (`@live` skipped) | every commit |
| Live eval | `evals/run_golden.py` + Phoenix | EV-001 Tier 3 | Claude | before release |
| Frontend | ESLint + TypeScript `tsc --noEmit`; manual journey checklist | Build safety + UJ-1..UJ-5 | — | every commit / release |
| Smoke (prod) | curl script | `/api/health`, one assessment, PDF, share | Claude | after each deploy |

## Test data
Golden cases only; no real personal data anywhere.

## Fakes
`FakeChatModel` returns queued structured outputs per node name, records call counts, and can raise to
simulate timeouts. Injected via a `get_llm()` dependency so production code paths are unchanged.

## Database in tests
API tests use a dedicated `pytest` schema inside the local `health_advisor` database (no CREATEDB
privilege needed), migrated with Alembic at session start, truncated per test, dropped at the end.

## Coverage target
Rules and safety modules ≥ 95% line coverage; overall backend ≥ 80%.

## Manual release checklist (Phase 9)
- [x] UJ-1 Meena end to end in browser (2026-10-10); share link opened in a second tab and revoked; PDF content verified by tests (visual layout: reviewer to check)
- [x] UJ-2 Priya referral, 0 LLM calls (FakeLLM in AC-2 scenario; Phoenix trace showed no LLM spans)
- [x] UJ-3 Joseph urgent banner in page and PDF
- [x] Keyboard-only run of the form (Q-08); [ ] VoiceOver pass — not done, recommended before launch
- [x] Mobile width 360 px — no horizontal overflow on landing, step 1, report (Q-08)
