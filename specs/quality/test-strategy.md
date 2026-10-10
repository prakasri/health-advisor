---
id: TS-001
title: Test strategy
status: draft
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
| Acceptance | pytest-bdd over `specs/functional/acceptance/*.feature` | AC-1 – AC-8 | fake model (`@live` skipped) | every commit |
| Live eval | `evals/run_golden.py` + Phoenix | EV-001 Tier 3 | Claude | before release |
| Frontend | ESLint + TypeScript `tsc --noEmit`; manual journey checklist | Build safety + UJ-1..UJ-5 | — | every commit / release |
| Smoke (prod) | curl script | `/api/health`, one assessment, PDF, share | Claude | after each deploy |

## Test data
Golden cases only; no real personal data anywhere.

## Fakes
`FakeChatModel` returns queued structured outputs per node name, records call counts, and can raise to
simulate timeouts. Injected via a `get_llm()` dependency so production code paths are unchanged.

## Database in tests
Tests use a separate database `health_advisor_test`, migrated at session start and truncated per test.

## Coverage target
Rules and safety modules ≥ 95% line coverage; overall backend ≥ 80%.

## Manual release checklist (Phase 9)
- [ ] UJ-1 Meena end to end in browser, PDF opens, share link works in a private window
- [ ] UJ-2 Priya referral, Phoenix shows 0 LLM spans
- [ ] UJ-3 Joseph urgent banner in page and PDF
- [ ] Keyboard-only run of the form; labels read correctly with VoiceOver
- [ ] Mobile width 360 px
