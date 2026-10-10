---
id: PRD-001
title: Product requirements (MVP)
status: approved
version: 1.0.0
depends_on: [VIS-001]
last_reviewed: 2026-10-10
---

# PRD-001 Product requirements

## 1. Features

| ID | Feature | MVP | Spec |
| --- | --- | --- | --- |
| F1.1 | HbA1c input with validation (3.0–20.0 %, one decimal) | ✔ | FS-F1 |
| F1.2 | Rule-based classification | ✔ | FS-F1, CLS-001 |
| F1.3 | Eligibility screen (age ≥ 18, not pregnant, not type 1) | ✔ | FS-F1, GR-001 |
| F1.4 | Urgent flag at HbA1c ≥ 10.0 | ✔ | FS-F1 |
| F1.5 | mmol/mol input | V1 | — |
| F2.1 | Comorbidity multi-select (8 + None, exclusive) | ✔ | FS-F2 |
| F2.2 | Family history | ✔ | FS-F2 |
| F2.3 | Diet preference + region | ✔ | FS-F2 |
| F2.4 | Age, gender, height, weight, auto BMI | ✔ | FS-F2, CLS-001 |
| F2.5 | Activity, smoking, alcohol | ✔ | FS-F2 |
| F3.1 | Calorie target | ✔ | FS-F3, CLS-001 |
| F3.2 | Diet plan (LLM) | ✔ | FS-F3, AI-001 |
| F3.3 | Lifestyle plan (LLM) | ✔ | FS-F3, AI-001 |
| F3.4 | Comorbidity adjustments | ✔ | FS-F3, CLS-001 |
| F3.5 | 7-day meal plan + grocery list | V1 | — |
| F4.1 | Lab tests with why / frequency / risk indicators | ✔ | FS-F4 |
| F4.2 | Screenings | ✔ | FS-F4 |
| F4.3 | Reminders | V2 | — |
| F5.1 | 10-section report | ✔ | FS-F5 |
| F5.2 | PDF download | ✔ | FS-F5 |
| F5.3 | Share link (30 days, revocable) | ✔ | FS-F5 |
| F5.4 | Feedback (helpful yes/no) | ✔ (descope #1) | FS-F5 |

## 2. Non-functional requirements

| ID | Requirement | Target |
| --- | --- | --- |
| NFR-1 | End-to-end assessment latency | p95 < 30 s |
| NFR-2 | Step-1 classification latency | p95 < 300 ms |
| NFR-3 | PDF generation | < 5 s |
| NFR-4 | Accessibility | WCAG 2.2 AA for forms and report (labels, keyboard, contrast) |
| NFR-5 | Privacy | No personal identifiers stored; 90-day retention |
| NFR-6 | Security | HTTPS everywhere; secrets in SSM; rate limit 10 assessments/min/IP |
| NFR-7 | Observability | 100% of graph runs traced in Phoenix |
| NFR-8 | Availability | Best effort (single EC2) for MVP |
| NFR-9 | Browser support | Latest Chrome, Safari, Firefox, Edge; mobile width ≥ 360 px |

## 3. Acceptance criteria (summary — executable versions in `functional/acceptance/`)

| ID | Criterion |
| --- | --- |
| AC-1 | 5.6 → normal; 5.7 → prediabetes; 6.4 → prediabetes; 6.5 → diabetes; 2.9 and 20.1 → 422 |
| AC-2 | Age 17, pregnant, or type 1 → referral report, 0 LLM spans |
| AC-3 | HbA1c ≥ 10.0 → urgent banner first in report and PDF |
| AC-4 | Vegetarian/vegan → no forbidden foods in any meal |
| AC-5 | Kidney disease → protein/potassium caution in diet, nephrologist question, eGFR + urine ACR in monitoring |
| AC-6 | Calorie target in report equals rule value |
| AC-7 | All 10 sections + disclaimer; no banned terms |
| AC-8 | PDF < 5 s; share link opens without login, expires after 30 days, 404 after revocation |
| AC-9 | p95 assessment < 30 s |
| AC-10 | 20/20 golden cases pass rule checks; safety pass rate ≥ 95% |

## 4. Out of scope (MVP)
Accounts, history, reminders, chat, OCR, translation, admin UI, mobile apps, medication advice.
