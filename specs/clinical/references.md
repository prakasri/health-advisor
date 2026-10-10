---
id: CLS-001-REF
title: Clinical references
status: draft
version: 1.0.0
depends_on: [CLS-001]
last_reviewed: 2026-10-10
---

# Clinical references

Every rule in this folder must trace to a source below. **Status `to verify`** means the value was
drafted from general knowledge and has not yet been checked against the current edition. Verifying
them (and setting `verified: true` in `monitoring-rules.yaml`) is part of the Phase 1 exit check.

| Rule | Value | Intended source | Status |
| --- | --- | --- | --- |
| HbA1c bands | < 5.7 / 5.7–6.4 / ≥ 6.5 % | American Diabetes Association, *Standards of Care in Diabetes*, section 2 "Diagnosis and Classification" | to verify |
| Diagnosis needs confirmation | Repeat test unless clear clinical diagnosis | ADA Standards of Care, section 2 | to verify |
| HbA1c unreliable in pregnancy, haemoglobinopathies, anaemia, CKD | Caveat in report | ADA Standards of Care, section 2 | to verify |
| Urgent threshold | ≥ 10 % → see doctor soon | Clinical judgement; ADA notes very high A1C/symptomatic hyperglycaemia needs prompt treatment (section 9) | to verify |
| Asian BMI cut-offs | 23 / 25 | WHO Expert Consultation, *Lancet* 2004;363:157–63; ICMR guidelines | to verify |
| Mifflin–St Jeor | Formula | Mifflin MD et al., *Am J Clin Nutr* 1990;51:241–7 | to verify |
| Activity factors | 1.2–1.725 | Standard Harris–Benedict activity multipliers | to verify |
| Calorie floors | 1200 / 1500 | Common clinical minimums for unsupervised energy restriction | to verify |
| 150 min/week activity | Walking goal baseline | ADA Standards of Care, section 5 "Facilitating Positive Health Behaviors"; WHO physical activity guidelines 2020 | to verify |
| Monitoring frequencies | See `monitoring-rules.yaml` | ADA Standards of Care, sections 2, 6, 10, 11, 12, 4 (comprehensive evaluation) | to verify |
| Prediabetes yearly testing; normal every 3 years | | ADA Standards of Care, section 2 | to verify |
| Sodium < 2,300 mg/day | Hypertension, CVD | ADA Standards of Care section 10; AHA | to verify |
| DASH pattern | Hypertension | NHLBI DASH eating plan | to verify |
| Protein not increased in CKD | Kidney disease | ADA Standards of Care section 11; KDIGO diabetes in CKD guideline | to verify |
| Fatty liver: 7–10 % weight loss, FIB-4 | Fatty liver | ADA Standards of Care section 4; AASLD guidance | to verify |
| Indian diet patterns | Meal examples | ICMR-NIN *Dietary Guidelines for Indians* (2024) | to verify |
