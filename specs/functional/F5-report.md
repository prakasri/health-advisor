---
id: FS-F5
title: F5 AI health report, PDF, share link, feedback
status: approved
version: 1.0.0
depends_on: [DM-001, GR-001, AI-001]
implements: [F5.1, F5.2, F5.3, F5.4]
last_reviewed: 2026-10-10
---

# FS-F5 AI health report

## F5.1 Report sections (order is fixed)

| # | Section | Schema field | Source |
| --- | --- | --- | --- |
| — | Urgent banner (only if urgent) | status.urgent | rules |
| — | Disclaimer (top) | disclaimer | GR-001 §5 |
| 1 | Overall Health Summary | summary | LLM (narrative) |
| 2 | Diabetes Status | status | rules |
| 3 | Identified Risk Factors | risk_factors | rules |
| 4 | Comorbidity Assessment | comorbidity_assessment | LLM (narrative); "No other conditions reported" if empty |
| 5 | Dietary Guidance | diet | rules + LLM |
| 6 | Lifestyle Guidance | lifestyle | LLM |
| 7 | Monitoring Recommendations | monitoring | rules |
| 8 | Preventative Actions | preventive_actions | LLM (narrative) |
| 9 | Questions to Discuss with a Doctor | doctor_questions | required (rules) + LLM, required first, de-duplicated |
| 10 | Medical Disclaimer | disclaimer + HbA1c accuracy caveat | GR-001 §5 |
| — | Footer | meta | rules_version, model_id, prompt_version, date |

Referral reports (`kind=referral`) show: referral message, HbA1c value, disclaimer, "Start again".

## F5.2 PDF
- `GET /api/reports/{id}/pdf`, `Content-Disposition: attachment; filename="health-report-YYYY-MM-DD.pdf"`.
- Rendered server-side with WeasyPrint from `backend/app/report/templates/report.html` (same section
  order as above, A4, print CSS). Generated on request, not stored.
- Target < 5 s. WeasyPrint is warmed up at API start-up (first cold render ≈ 5 s, then ≈ 0.3 s).

## F5.3 Share link
- `POST /api/reports/{id}/share` → token (`secrets.token_urlsafe(32)`), `expires_at = now + 30 days`,
  `url_path = /share/<token>`.
- `GET /api/share/{token}` → report, increments `view_count`; 404 if unknown, expired or revoked.
- `DELETE /api/share/{token}` → revoke. The token is the only credential (no accounts, ADR 0002), so anyone holding the link could revoke it; acceptable for the MVP and noted in VIS-001 accepted risks.
- Shared page: read-only, `<meta name="robots" content="noindex">`, PDF download allowed.

## F5.4 Feedback
"Was this report helpful?" Yes/No + optional comment (≤ 500 chars). One submission per page load.
