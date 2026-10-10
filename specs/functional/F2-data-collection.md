---
id: FS-F2
title: F2 Clinical data collection
status: draft
version: 1.0.0
depends_on: [DM-001, CLS-001]
implements: [F2.1, F2.2, F2.3, F2.4, F2.5]
last_reviewed: 2026-10-10
---

# FS-F2 Clinical data collection

Collected in form steps 2 and 3 (UJ-001). Submitted together with step-1 fields as one
`AssessmentInput` (schema DM-001) to `POST /api/assessments`.

## Step 2 — health history
| Field | Control | Options | Rule |
| --- | --- | --- | --- |
| comorbidities | Checkbox group | Hypertension (high blood pressure), Dyslipidemia (high cholesterol), Obesity, Cardiovascular disease, Kidney disease, Thyroid disorder, Fatty liver disease, Sleep apnoea, None | At least one; ticking None clears others; ticking any other clears None |
| family_history | Yes/No radio | Parent or sibling with diabetes | Required |

## Step 3 — lifestyle and diet
| Field | Control | Options / range | Notes |
| --- | --- | --- | --- |
| gender | Radio | Female, Male, Other / prefer not to say | Asked in step 1 (drives pregnancy question); shown read-only here |
| height_cm | Number | 100–250 | Unit toggle cm / ft-in (converted client-side) |
| weight_kg | Number | 25–300 | Unit toggle kg / lb |
| BMI | Read-only | — | Computed live with CLS-001 §4 (display only; server recomputes) |
| activity | Radio with descriptions | Sedentary (mostly sitting), Lightly active (light walking 1–3 days/week), Moderately active (exercise 3–5 days/week), Very active (hard exercise 6–7 days/week) | |
| smoking | Radio | Never, Former, Current | |
| alcohol | Radio | None, Occasional (a few drinks a month), Regular (most weeks) | |
| diet | Radio | Vegetarian, Non-vegetarian, Vegan | |
| region | Select | Indian, Mediterranean, East Asian, Western | Default by browser locale (en-IN → Indian), user can change |

## Server behaviour
- Validate with `assessment-input.schema.json`; 422 on failure with field paths.
- BMI and categories are always recomputed server-side; client values are ignored.
