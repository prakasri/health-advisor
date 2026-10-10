---
id: VIS-001
title: Product vision
status: draft
version: 1.0.0
depends_on: []
last_reviewed: 2026-10-10
---

# VIS-001 Product vision

## Vision
Help anyone who knows their HbA1c understand what it means and what to do next — in a 5-minute,
personalised, evidence-based plan they can take to their doctor.

## Problem
People receive an HbA1c number with little context. Generic advice ignores their diet, culture and
other conditions, and they often don't know which follow-up tests to ask for.

## Solution
A web app that turns an HbA1c value and a short health profile into:
1. a clear, non-diagnostic status (normal / prediabetes / diabetes range),
2. a practical diet and lifestyle plan that fits their diet preference, region and conditions,
3. a checklist of tests, screenings and questions for their next appointment,
delivered as a 10-section report with PDF download and a shareable link.

## Personas

| Persona | Situation | Wants |
| --- | --- | --- |
| Ravi, 45 | HbA1c 6.1, sedentary office job, family history, non-vegetarian, Indian | "How do I stop this becoming diabetes?" |
| Meena, 58 | HbA1c 7.8, high blood pressure, vegetarian, Indian | "What should I eat, and which tests am I missing?" |
| Alex, 30 | HbA1c 5.3, smoker, very active, Western | "Am I fine, and how do I stay that way?" |

## Scope

| In | Out |
| --- | --- |
| Adults (18+) entering an HbA1c they already have | Diagnosis of diabetes or its type |
| Educational classification using ADA thresholds | Medication, insulin or dose advice |
| Diet, lifestyle, monitoring and screening guidance | Pregnancy, under-18s, type 1 diabetes (referral page) |
| Report to discuss with a clinician | Accounts, stored identity, history (V1+) |

## Principles
1. **Rules for facts, AI for personalisation** (ADR 0001).
2. **Never diagnose** — "in the … range", never "you have …".
3. **Always point to a professional** — disclaimer and doctor questions in every report.
4. **Explain why** — every recommendation shows the inputs it was based on.
5. **Culturally real food** — meals match diet preference and region.
6. **Privacy by default** — no identity collected (ADR 0002).

## Success (MVP / academic submission)
All MVP acceptance criteria in PRD-001 pass, and the system is live on Vercel + AWS with Phoenix traces.

## Known accepted risks (MVP)
- Report and share URLs are bearer links: anyone holding one can read the report. Mitigated by no
  stored identity, unguessable IDs, 30-day share expiry and 90-day retention.
- Share links are bearer tokens: whoever holds a link can view the report and can also revoke the link
  (there are no accounts to tie it to an owner). Mitigated by 30-day expiry and 256-bit tokens.
- Clinical rule values await verification against the current ADA Standards of Care (CLS-001-REF).
