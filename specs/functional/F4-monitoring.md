---
id: FS-F4
title: F4 Monitoring and follow-up
status: draft
version: 1.0.0
depends_on: [CLS-001]
implements: [F4.1, F4.2]
last_reviewed: 2026-10-10
---

# FS-F4 Monitoring and follow-up

Entirely rule-based (`plan_monitoring`, CLS-001 §7, `monitoring-rules.yaml`). No LLM involvement.

## Output per item
`MonitoringItem`: id, name, kind (lab | screening), why, frequency, risk_indicators, highlighted.

`risk_indicators` lists the item's indicators; `highlighted = true` when the user's inputs match any
`highlight_when` condition. The report shows highlighted items first with a "Higher priority for you"
tag and the matching indicator(s).

## Expected coverage by classification (no comorbidities, no other risk factors)

| Classification | Labs | Screenings |
| --- | --- | --- |
| normal | HbA1c (screening) | Blood pressure |
| prediabetes | HbA1c (yearly), fasting blood sugar | Blood pressure |
| diabetes | HbA1c, fasting, post-meal, lipid profile, kidney function, vitamin B12 | Eye, foot, blood pressure, cardiovascular assessment |

Comorbidities add items (e.g. kidney disease → kidney function + vitamin D; fatty liver → liver function;
thyroid disorder → TSH).

## Rules
- No duplicate names in output.
- Order: highlighted first; then labs; then screenings; each in file order.
- Frequencies are shown exactly as written in the YAML.
