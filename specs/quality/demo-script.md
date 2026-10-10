---
id: DEMO-001
title: Demo script (5 minutes)
status: approved
version: 1.0.0
depends_on: [UJ-001, AC-EVIDENCE]
last_reviewed: 2026-10-10
---

# Demo script — 5 minutes

**Before recording:** start the API (with the Anthropic key), Phoenix and the frontend (README →
Local development). Open three tabs: the app, Phoenix (project `health-advisor`), and this repo in
your editor. Create one AI report beforehand as a backup in case the network is slow.

| Time | Show | Say |
| --- | --- | --- |
| 0:00–0:40 | `specs/00-index.md` and the traceability matrix; `specs/clinical/clinical-rules.yaml` | "This was built specification-first: every requirement traces to a spec, a test and code. Clinical rules live in versioned YAML checked against the ADA Standards of Care 2026 — the code reads them, it never hard-codes them." |
| 0:40–2:20 | The app: Meena — HbA1c 7.8, 58, female, high blood pressure, 155 cm / 68 kg, sedentary, vegetarian, Indian | Point out: instant classification after step 1, live BMI with Asian cut-offs, progress screen. On the report: urgent-free summary, vegetarian low-sodium Indian meals, 1,200 kcal from the rules, highlighted tests with "why it matters for you", doctor questions, disclaimer. |
| 2:20–2:50 | Download PDF; create a share link, open it in a private window, Stop sharing, reload | "Shareable without accounts: a 256-bit link that expires in 30 days and can be revoked." |
| 2:50–3:20 | New assessment: pregnant user (HbA1c 6.0) | "Safety exits run before any AI: pregnant, under-18 and type 1 users get a referral — and no model call is made." |
| 3:20–4:10 | Phoenix: open Meena's trace | Show rule nodes, the three writers running in parallel, the safety check with the LLM judge. "Clinical facts are deterministic; the model only writes the personalised text, and a safety layer checks it — with one retry and a safe fallback." |
| 4:10–5:00 | `specs/quality/eval-results/2026-10-10T1142Z.md` and a terminal running `cd backend && uv run pytest -q` | "16 golden cases on the live model: zero unsafe reports, 100% delivered, p95 25 seconds. 267 automated tests, including the Gherkin acceptance criteria themselves, at 97% coverage." |

**If something fails live:** use the pre-made report; the eval results file and the test run carry
the evidence on their own.
