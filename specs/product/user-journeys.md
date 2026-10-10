---
id: UJ-001
title: User journeys
status: approved
version: 1.0.0
depends_on: [VIS-001, PRD-001]
last_reviewed: 2026-10-10
---

# UJ-001 User journeys

## UJ-1 Main journey (about 5 minutes)

| Step | Screen | User does | System does |
| --- | --- | --- | --- |
| 1 | Landing `/` | Reads purpose and disclaimer, ticks "I understand this is not medical advice", clicks Start | — |
| 2 | Step 1 `/assess/step-1` | Enters HbA1c %, age, pregnancy (shown if gender female/other), type 1 yes/no | `POST /api/classify` |
| 3 | Step 1 result | Sees "Your HbA1c is in the … range" card with explanation; urgent banner if ≥ 10 | — |
| 4 | Step 2 `/assess/step-2` | Selects comorbidities (or None), family history | Client validation |
| 5 | Step 3 `/assess/step-3` | Height, weight (BMI shown live), gender, activity, smoking, alcohol, diet, region | Client validation |
| 6 | Generating | Waits; sees progress steps ("Checking your results", "Building your food plan", "Safety review") | `POST /api/assessments` |
| 7 | Report `/report/[id]` | Reads the 10 sections | `GET /api/reports/{id}` |
| 8 | Actions | Downloads PDF, creates share link, gives feedback | `/pdf`, `/share`, `/feedback` |

Form state is kept in the browser (sessionStorage) between steps; nothing is sent until step 1 submit
and step 3 submit.

## UJ-2 Ineligible exit
At step 2 of UJ-1, if `eligible = false` the user goes to `/assess/referral` showing the referral message
for their reason, their HbA1c value, the disclaimer, and a "Start again" link. No further steps, no LLM call.
(The full submission also returns a `kind=referral` report if an ineligible payload reaches `/assessments`.)

## UJ-3 Urgent flag
HbA1c ≥ 10.0: the step-1 card and the top of the report and PDF show the urgent message in a warning
style. The journey otherwise continues normally.

## UJ-4 AI failure
If the LLM fails safety twice or is unavailable, the report is built from rule-only fallback content.
The user sees the same 10 sections; the footer notes "Some sections use standard guidance".

## UJ-5 Shared report
Recipient opens `/share/[token]`: read-only report and PDF download, no actions except "Start your own
assessment". Expired or revoked → "This link is no longer available".

## Persona walk-throughs (golden cases G01–G05 in EV-001)

| Persona | Inputs | Path | Expected emphasis |
| --- | --- | --- | --- |
| Ravi, 45 | 6.1, sedentary, 172 cm / 80 kg, family history, non-veg, Indian | UJ-1 | Prediabetes; obese (Asian BMI 27.0); 500 kcal deficit; walking goal; yearly HbA1c |
| Meena, 58 | 7.8, hypertension, 155 cm / 68 kg, vegetarian, Indian | UJ-1 | Diabetes range; low-sodium vegetarian meals; eye, foot, kidney checks; BP |
| Alex, 30 | 5.3, smoker, very active, Western | UJ-1 | Normal; stop smoking first; HbA1c every 3 years |
| Priya, 29 | 6.0, pregnant | UJ-2 | Referral; no LLM call |
| Joseph, 62 | 11.2, kidney disease + obesity | UJ-1 + UJ-3 | Urgent banner; protein/potassium caution; nephrologist question |
