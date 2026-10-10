---
id: AC-EVIDENCE
title: Acceptance criteria — evidence
status: approved
version: 1.0.0
depends_on: [PRD-001, AC-001, EV-001, TS-001]
last_reviewed: 2026-10-10
---

# Acceptance criteria — evidence

All ten MVP acceptance criteria in PRD-001 are met locally. The Gherkin files in
`functional/acceptance/` run as tests (`backend/tests/bdd/test_acceptance.py`, pytest-bdd): 33
scenarios pass, and the `@live` latency scenario is evidenced by the live evaluation instead.

| AC | Criterion (PRD-001) | Status | Evidence |
| --- | --- | --- | --- |
| AC-1 | 5.6 → normal; 5.7 → prediabetes; 6.4 → prediabetes; 6.5 → diabetes; 2.9 and 20.1 → 422 | Met | `classification.feature` (incl. 5.65 and 6.45 rounding); `test_rules.py::test_classification_boundaries`; golden G06–G09, G17, G18 |
| AC-2 | Age 17, pregnant or type 1 → referral report, 0 LLM spans | Met | `classification.feature` "Ineligible users…" asserts zero FakeLLM calls; Phoenix trace of a referral showed no LLM spans; browser: Priya |
| AC-3 | HbA1c ≥ 10.0 → urgent banner first in report and PDF | Met | `classification.feature` "Urgent message leads the report" (checks PDF text order); `test_report_outputs.py::test_urgent_pdf_leads_with_the_urgent_message`; browser: Joseph |
| AC-4 | Vegetarian/vegan → no forbidden foods in any meal | Met | `recommendations.feature` S3 scenarios; `test_safety.py` (incl. regressions from live runs); live eval: 0 diet violations shown |
| AC-5 | Kidney disease → protein/potassium caution, nephrologist question, eGFR + urine ACR | Met | `recommendations.feature` "Kidney disease adjustments"; browser: Joseph's report |
| AC-6 | Calorie target in report equals rule value | Met | `recommendations.feature` calorie scenarios (S4); golden cases (exact kcal); PDF test checks "1,200 kcal" |
| AC-7 | All 10 sections + disclaimer; no banned terms | Met | `recommendations.feature` "Complete report" and banned-language scenarios; schema validation of every golden case; PDF test checks all 10 section titles |
| AC-8 | PDF < 5 s; share link opens without login, expires after 30 days, 404 after revocation | Met | `report.feature` (PDF, share, revoke, expiry); `test_report_outputs.py`; first PDF after start-up 0.28 s; browser: share → open → stop sharing → "no longer available" |
| AC-9 | p95 assessment < 30 s | Met | EV-001 Tier 3 run `eval-results/2026-10-10T1142Z.md`: p95 25.2 s, median 19.2 s (16 cases, claude-sonnet-5) |
| AC-10 | 20/20 golden cases pass rule checks; safety pass rate ≥ 95% | Met | `test_golden_rules.py` 20/20 exact; live eval: 100% delivered without fallback, 94% first-attempt, 0 unsafe reports shown |

## Test totals at the end of Phase 9
- Backend: 267 passed, 1 skipped (`@live`), coverage 97% (`uv run pytest --cov=app`).
- Frontend: `npm run typecheck`, `npm run lint`, `next build` clean.
- Accessibility: Q-08 — 14 of 15 checks pass; a screen-reader pass is recommended before launch.

## Not yet evidenced (needs deployment, Phase 5/8)
- Smoke test against the live Vercel + AWS URL.
- Production traces in Phoenix.
