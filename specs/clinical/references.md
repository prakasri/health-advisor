---
id: CLS-001-REF
title: Clinical references
status: draft
version: 1.1.0
depends_on: [CLS-001]
last_reviewed: 2026-10-10
---

# Clinical references

Primary source: American Diabetes Association, *Standards of Care in Diabetes—2026*, Diabetes Care
49(Supplement 1), January 2026 —
[section 2, Diagnosis and Classification](https://diabetesjournals.org/care/article/49/Supplement_1/S27/163926/2-Diagnosis-and-Classification-of-Diabetes),
[Summary of Revisions](https://diabetesjournals.org/care/article/49/Supplement_1/S6/163930/Summary-of-Revisions-Standards-of-Care-in-Diabetes),
[section 3, Prevention or Delay](https://diabetesjournals.org/care/article/49/Supplement_1/S50/163924/3-Prevention-or-Delay-of-Diabetes-and-Associated).

**Status key**
- `secondary-2026` — value matches published summaries of the 2026 Standards, checked on 2026-10-10.
  The primary journal text blocks automated access, so a human should still confirm it against the
  section named before public launch (not required for the academic submission).
- `to verify` — not yet checked; drafted from general knowledge.
- `judgement` — a product decision, not a guideline value; documented here so it can be reviewed.

| Rule | Value in specs | Source (2026 Standards unless stated) | Status |
| --- | --- | --- | --- |
| HbA1c bands | < 5.7 / 5.7–6.4 / ≥ 6.5 % | §2 Diagnosis | secondary-2026 |
| Repeat test to confirm diagnosis | Wording in report | §2 Diagnosis | to verify |
| HbA1c less reliable (pregnancy, haemoglobin variants, anaemia, CKD, transfusion) | Report caveat | §2 Diagnosis | to verify |
| Normal result → retest at least every 3 years | `hba1c_screening` | §2 Screening | secondary-2026 |
| Prediabetes → test at least annually | `hba1c_prediabetes` | §2 / §3 | secondary-2026 |
| Diabetes → A1C at least twice a year at goal; about every 3 months if not at goal or treatment changed | `hba1c_diabetes` | §6 Glycemic Goals | secondary-2026 |
| Urgent flag at ≥ 10 % | `urgent_threshold` | Product decision; §9 notes A1C ≥ 10 % as a level where prompt intensified treatment is considered | judgement |
| Lipid profile at diagnosis and annually (≥ every 5 years if < 40) | `lipid_profile` | §10 Cardiovascular Disease | secondary-2026 |
| UACR + eGFR at least annually in type 2 diabetes | `kidney_function` | §11 Chronic Kidney Disease | secondary-2026 |
| FIB-4 screening in prediabetes/T2D with obesity or cardiometabolic risk; repeat every 1–2 years if low risk | `liver_function` | §4 Comprehensive Medical Evaluation (MASLD) | secondary-2026 |
| B12 monitoring (annually) with long-term metformin | `vitamin_b12` | §9 Pharmacologic Approaches | secondary-2026 |
| Dilated eye exam at diagnosis, then annually; every 1–2 years if no retinopathy and well controlled | `eye_exam` | §12 Retinopathy | secondary-2026 |
| Comprehensive foot evaluation at least annually | `foot_exam` | §12 Foot Care | secondary-2026 |
| Fasting / post-meal glucose | `fasting_glucose`, `postprandial_glucose` | §2, §7 | to verify |
| Blood pressure at every visit | `blood_pressure` | §10 | to verify |
| Annual cardiovascular risk assessment | `cardiovascular_assessment` | §10 | to verify |
| Vitamin D only if indicated | `vitamin_d` | Not routinely recommended (judgement) | judgement |
| TSH 6–12 monthly in thyroid disorder | `thyroid_function` | Endocrine practice norm, not ADA | judgement |
| Asian BMI cut-offs 23 / 25 | `clinical-rules.yaml → bmi` | WHO Expert Consultation, *Lancet* 2004;363:157–63; ADA uses BMI ≥ 23 for screening Asian Americans (§2) | to verify |
| Mifflin–St Jeor BMR | `calories.bmr` | Mifflin MD et al., *Am J Clin Nutr* 1990;51:241–7 | to verify |
| Activity factors 1.2–1.725 | `calories.activity_factor` | Standard activity multipliers | to verify |
| Calorie floors 1200 / 1500 | `calories.floor_kcal` | Common minimums for unsupervised restriction | judgement |
| 150 min/week moderate activity | Lifestyle prompt, fallback | §5 Facilitating Positive Health Behaviors; WHO 2020 | to verify |
| Sodium < 2,300 mg/day | Hypertension, CVD constraints | §5 / §10 | to verify |
| Protein not increased in CKD | Kidney constraint | §11; KDIGO 2022 diabetes-in-CKD guideline | to verify |
| Fatty liver: 7–10 % weight loss | Fatty-liver constraint | §4 | to verify |
| Indian diet patterns | Meal examples | ICMR-NIN *Dietary Guidelines for Indians* (2024) | to verify |

## Secondary sources consulted (2026-10-10)
Search-result summaries citing the 2026 Standards, including
[open-exam-prep diagnosis guide](https://open-exam-prep.com/study-guides/fnp/endocrine/diabetes-diagnosis),
[iatrox prediabetes screening guidance](https://www.iatrox.com/clinical-guidance/us/prediabetes-type-2-diabetes-screening-diagnosis),
[ACC UACR screening case (2026)](https://www.acc.org/Education-and-Meetings/Patient-Case-Quizzes/2026/06/02/11/11/UACR-Screening-During-a-Routine-Annual-Visit),
[iatrox diabetic foot guidance](https://www.iatrox.com/clinical-guidance/us/diabetic-foot-problems),
[AACE MASLD testing 2026](https://pro.aace.com/pdfs/presentations/thursday/MASLD-Testing-2026-Kanwal.pdf),
[NIDDK metformin and B12](https://www.niddk.nih.gov/health-information/professionals/diabetes-discoveries-practice/metformin-vitamin-b12-deficiency).
