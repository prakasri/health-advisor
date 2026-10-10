---
id: FS-F1
title: F1 Diabetes classification engine
status: approved
version: 1.0.0
depends_on: [CLS-001, GR-001]
implements: [F1.1, F1.2, F1.3, F1.4]
last_reviewed: 2026-10-10
---

# FS-F1 Diabetes classification engine

**Endpoint:** `POST /api/classify` (rules only, no LLM, no DB write).

## Inputs
| Field | Type | Validation | Error message (UI) |
| --- | --- | --- | --- |
| hba1c | number | 3.0–20.0; UI accepts one decimal | "Enter your HbA1c as a percentage between 3.0 and 20.0, for example 6.2" |
| age | integer | 1–120 | "Enter your age in years" |
| pregnant | boolean | required (UI asks only when gender is female or other; otherwise sends false) | — |
| type1_diabetes | boolean | required | — |

## Processing
1. Round hba1c to 1 decimal (half up).
2. Eligibility per CLS-001 §1. If ineligible → return `eligible=false`, `exit_reason`, `referral_message`; no classification.
3. Classification per CLS-001 §2; `label`, `explanation` from `clinical-rules.yaml`.
4. `urgent = hba1c ≥ 10.0`; `urgent_message` when true.

## Output
`ClassifyResponse` in `openapi.yaml`.

## Edge cases
| Input | Result |
| --- | --- |
| 5.65 | rounds to 5.7 → prediabetes |
| 6.44 | rounds to 6.4 → prediabetes |
| 6.45 | rounds to 6.5 → diabetes |
| 9.9 / 10.0 | not urgent / urgent |
| age 18 | eligible |
| age 17 + pregnant | exit_reason = under_18 (first rule wins) |
| "6,5" (comma) | UI normalises to 6.5 before sending |
