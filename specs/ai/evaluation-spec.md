---
id: EV-001
title: Evaluation — golden cases and LLM quality
status: draft
version: 1.0.0
depends_on: [CLS-001, GR-001, AI-001]
implements: [AC-10]
last_reviewed: 2026-10-10
---

# EV-001 Evaluation

## 1. Golden cases
`specs/quality/golden-cases.jsonl` — 20 cases (G01–G20) covering the five personas, every HbA1c
boundary (5.6, 5.65, 5.7, 6.4, 6.45, 6.5, 9.9, 10.0), all three exits (including the precedence case
G14), every comorbidity, all diets, all regions, underweight through obese, and all three genders.

Expected values are produced by `specs/quality/golden_oracle.py`, an independent reference written from
the spec text (not by importing app code), then reviewed by hand. Regenerate after any rule change.

## 2. Tier 1 — rule evaluation (deterministic, every commit)
`backend/tests/test_golden_rules.py` runs the rule nodes for each case and asserts exact equality on:
`eligible, exit_reason, hba1c_rounded, classification, urgent, bmi, bmi_category, calorie_target,
risk_factor_ids, monitoring_ids, constraint_checks, required_doctor_question_count`.
**Pass = 20/20.**

## 3. Tier 2 — graph evaluation with stub LLM (every commit)
LLM nodes replaced by a fake model returning fixed valid / invalid outputs. Asserts: routing, retry
once, fallback after second failure, 0 LLM calls for ineligible cases, report has all sections and
validates against `report.schema.json`.

## 4. Tier 3 — live LLM evaluation (manual / before release; needs API key)
`backend/evals/run_golden.py` runs the full graph on the 17 eligible cases, sends traces to Phoenix
(project `health-advisor`, dataset `golden-v1`), and records:

| Metric | How | Target |
| --- | --- | --- |
| Safety pass rate (first attempt) | `safety.passed` on attempt 1 | ≥ 85% |
| Safety pass rate (final) | not `used_fallback` | ≥ 95% |
| Diet-preference violations | GR-001 S3 | 0 |
| Number consistency | GR-001 S4 | 0 failures |
| Banned terms | GR-001 S2 | 0 |
| Latency p95 | span duration | < 30 s |
| Judge-graded quality | Phoenix LLM eval (relevance to profile, regional fit, readability) on a 1–5 rubric | mean ≥ 4 |

Results are saved to `specs/quality/eval-results/<date>.md` as submission evidence.

## 5. Regression rule
Any change to a prompt, the model, `banned-terms.yaml` or the rules requires Tier 1 + 2 green and a
Tier 3 run before merge to `main`.
