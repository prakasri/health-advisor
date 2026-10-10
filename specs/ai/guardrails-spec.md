---
id: GR-001
title: Guardrails — non-diagnostic language, safety exits, safety check, fallback
status: draft
version: 1.0.0
depends_on: [CLS-001, AI-001]
implements: [F1.3, F1.4, F3.2, F3.3, F3.4, F5.1]
last_reviewed: 2026-10-10
---

# GR-001 Guardrails

The product gives educational lifestyle guidance. It must never diagnose, never advise on
medication, and never contradict the rule engine. Guardrails are layered: **before** the LLM
(eligibility, constraints in the prompt), **in** the LLM (system prompt rules, structured output),
and **after** the LLM (`safety_check`, fallback).

## 1. Before the LLM

| ID | Guardrail | Where | Behaviour |
| --- | --- | --- | --- |
| G1 | Eligibility exit | `validate_input` | Under 18, pregnant or type 1 → referral report, **no LLM call** |
| G2 | Urgent flag | `classify` | HbA1c ≥ 10.0 → urgent banner first in report and PDF |
| G3 | Input validation | API + `validate_input` | Schema `assessment-input.schema.json`; out-of-range → HTTP 422 |
| G4 | Constraints as hard rules | `assess_risk` → prompts | Comorbidity diet/lifestyle lines are injected as MUST rules |
| G5 | Rule values are read-only | prompts | LLM receives classification, BMI, calorie target, monitoring as facts it must not change or restate differently |
| G6 | Minimum data to the LLM | prompts | No IDs, no free text from the user (the form has none in MVP) |

## 2. In the LLM (system prompt rules, shared by all three writer prompts)

1. You are writing educational wellness guidance, not medical advice.
2. Never say or imply the user has a disease. Use "your HbA1c is in the … range".
3. Never mention medication names, doses, or starting/stopping/changing any medicine. If medication is
   relevant, say "discuss with your doctor".
4. Never promise to cure, reverse or guarantee anything.
5. Use the numbers given (calorie target, BMI, HbA1c) exactly; do not compute new ones.
6. Follow every constraint in `constraints` exactly.
7. Respect the diet preference strictly (vegetarian: no meat, fish, egg; vegan: also no dairy or honey).
8. Use foods typical of the user's region; plain, warm, encouraging language; reading level about grade 8.
9. Output only the JSON structure requested.

## 3. After the LLM — `safety_check`

Runs over `diet_plan`, `lifestyle_plan` and `narrative`. Rule checks (R) always run; the LLM judge (J)
runs only if all rule checks pass.

| ID | Check | Type | Fails when |
| --- | --- | --- | --- |
| S1 | Schema | R | Pydantic validation of DietPlan / LifestylePlan / Narrative fails |
| S2 | Banned terms | R | Any `banned` pattern in `banned-terms.yaml` matches any string (`drug_names` allowed only in monitoring, which is rule-generated) |
| S3 | Diet preference | R | Any `diet_forbidden` word for the user's diet appears in meal options or `foods_to_eat`, after removing `diet_allow_phrases` |
| S4 | Numbers consistent | R | Any number followed by "kcal"/"calories" ≠ `calorie_target`; any HbA1c % ≠ input; any BMI ≠ computed |
| S5 | Constraint checks | R | `check: no_high_protein` (kidney_disease): text recommends "high protein", "protein shake", "protein powder" · `check: no_alcohol_encouraged` (fatty_liver): text suggests drinking alcohol in moderation |
| S6 | Doctor questions | R | Fewer than 3, or a comorbidity's `doctor_question` missing from the final report (assembled by code, so this guards regressions) |
| J1 | Judge | J | LLM judge (`prompts/safety_judge.v1.md`) returns `pass: false` on: diagnosis, medication advice, contradiction of constraints, unsafe exercise advice for stated conditions, or unkind/fear-based tone |

Result: `SafetyResult {passed: bool, failures: [{check, detail}]}` stored in state and traced in Phoenix.

## 4. Retry and fallback

1. First failure: re-run `write_diet_plan`, `write_lifestyle_plan` and `write_narrative` once, with the
   failure details appended to the prompt as "Fix these problems: …".
2. Second failure: `assemble_report` uses **rule-only fallback text** for the LLM sections:
   - Diet: constraints + generic plate-method guidance + region-neutral food lists from
     `specs/ai/fallback-content.yaml` filtered by diet preference.
   - Lifestyle: 150 min/week walking goal, sleep 7–9 h, two stress techniques, comorbidity lifestyle lines.
   - Narrative: template summary built from status, risk factors and monitoring.
   `meta.used_fallback = true`. The report is still complete (10 sections).
3. LLM unavailable (timeout 45 s / API error) → same fallback.

## 5. Disclaimer (exact text, top and bottom of every report and the PDF)

> This report is for educational and wellness purposes only. It is not a medical diagnosis and does
> not replace advice from a qualified healthcare professional. HbA1c results should be confirmed by
> your doctor. Do not start, stop or change any medication without medical advice.

Additional caveat on every full report: "HbA1c can be less accurate if you have anaemia, kidney
disease, a recent blood transfusion or certain haemoglobin variants."

Exact wording is stored in `specs/ai/report-text.yaml` (disclaimer, caveat, labels).

## 6. Transparency

- Sections written by AI are labelled "Personalised with AI".
- Footer shows `rules_version`, `model_id`, `prompt_version`.
- Each diet and lifestyle section lists `based_on` (the inputs that shaped it).
