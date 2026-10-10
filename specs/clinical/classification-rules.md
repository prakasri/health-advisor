---
id: CLS-001
title: Clinical rules — classification, metrics, risk factors, monitoring
status: approved
version: 1.0.0
depends_on: [VIS-001, DM-001]
implements: [F1.1, F1.2, F1.3, F1.4, F2.4, F3.1, F3.4, F4.1, F4.2]
last_reviewed: 2026-10-10
---

# CLS-001 Clinical rules

All clinical logic is **deterministic code** in `backend/app/rules/` that reads the YAML files in this
folder. The LLM never computes or changes these values (ADR 0001).

| File | Consumed by | Contents |
| --- | --- | --- |
| `clinical-rules.yaml` | `classify`, `compute_metrics`, `assess_risk` | Eligibility, HbA1c bands, urgent threshold, BMI cut-offs, calorie formula, risk factors |
| `monitoring-rules.yaml` | `plan_monitoring` | Lab tests and screenings with why, frequency, risk indicators |
| `comorbidity-constraints.yaml` | `assess_risk` → LLM prompts, `safety_check` | Diet and lifestyle constraints and a doctor question per comorbidity |

## 1. Eligibility (F1.3)

Evaluated in this order; the first match exits to the referral report with no LLM call.

| Order | Condition | Exit reason |
| --- | --- | --- |
| 1 | `age < 18` | `under_18` |
| 2 | `pregnant = true` | `pregnant` |
| 3 | `type1_diabetes = true` | `type1` |

Rationale: HbA1c thresholds and lifestyle guidance in this tool are for non-pregnant adults; pregnancy
and type 1 diabetes need specialist plans.

## 2. HbA1c classification (F1.2)

| HbA1c (%) | Classification | Label |
| --- | --- | --- |
| < 5.7 | `normal` | In the normal range |
| 5.7 – 6.4 | `prediabetes` | In the prediabetes range |
| ≥ 6.5 | `diabetes` | In the diabetes range |

- Input is rounded to one decimal place **before** classification (6.45 → 6.5).
- Lower bounds are inclusive: 5.7 is prediabetes, 6.5 is diabetes.
- Valid input range 3.0–20.0; outside → validation error (HTTP 422), not a classification.
- Wording rule: always "in the … range", never "you have …" (GR-001).

## 3. Urgent flag (F1.4)

`urgent = hba1c ≥ 10.0`. Shown as the first element of the report and the PDF, with the
`urgent_message` text. Does not block the report.

## 4. BMI (F2.4)

`bmi = weight_kg / (height_cm / 100)²`, rounded to 1 decimal.

| Category | Standard (WHO) | Asian (region = indian, east_asian) |
| --- | --- | --- |
| underweight | < 18.5 | < 18.5 |
| normal | 18.5 – 24.9 | 18.5 – 22.9 |
| overweight | 25.0 – 29.9 | 23.0 – 24.9 |
| obese | ≥ 30.0 | ≥ 25.0 |

## 5. Calorie target (F3.1)

1. BMR (Mifflin–St Jeor): `10 × kg + 6.25 × cm − 5 × age + c`, with c = +5 (male), −161 (female),
   −78 (other: mean of the two).
2. Maintenance = BMR × activity factor (1.2 / 1.375 / 1.55 / 1.725).
3. If BMI category is overweight or obese: subtract 500 kcal.
4. Apply floor: 1200 (female), 1500 (male), 1350 (other).
5. Round to the nearest 50 kcal.

Worked example (Meena): female, 58 y, 155 cm, 68 kg, sedentary, Indian → BMI 28.3 (obese, Asian).
BMR = 680 + 968.75 − 290 − 161 = 1197.75; × 1.2 = 1437.3; − 500 = 937.3 → floor 1200 → **1200 kcal**.

## 6. Risk factors

Defined in `clinical-rules.yaml → risk_factors`. Each produces `{id, label, triggered_by}`, where
`triggered_by` names the input value (e.g. `bmi=28.3 (asian cut-offs)`), so every factor is explainable.
One `comorbidity` factor is produced per selected comorbidity.

## 7. Monitoring (F4.1, F4.2)

Defined in `monitoring-rules.yaml`. An item is included if any `applies_when` condition matches
(keys within one condition are ANDed); `highlighted` if any `highlight_when` matches. Output order:
highlighted first, then labs, then screenings, each in file order. Duplicated ids never appear
(each HbA1c item applies to exactly one classification).

## 8. Comorbidity constraints (F3.4)

For each selected comorbidity, `assess_risk` copies its `diet` and `lifestyle` lines into
`diet_constraints` / `lifestyle_constraints` and its `doctor_question` into the report. Constraints are
passed to the LLM as **hard requirements** and checked by `safety_check` where a `check` is defined.

## 9. Change control

Changing any value requires: a PR editing the YAML + this file, a `version` bump, updated golden cases
(EV-001), and green tests. `rules_version` is stored in every report.
