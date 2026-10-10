---
id: INDEX
title: Specification index and traceability
status: approved
version: 1.0.0
last_reviewed: 2026-10-10
---

# Specification index

| ID | File | Status |
| --- | --- | --- |
| PLAN-001 | `00-build-plan.md` | approved |
| VIS-001 | `product/vision.md` | approved |
| PRD-001 | `product/prd.md` | approved |
| UJ-001 | `product/user-journeys.md` | approved |
| FS-F1..F5 | `functional/F1-classification.md` … `F5-report.md` | approved |
| AC-001 | `functional/acceptance/*.feature` (executed by `backend/tests/bdd/test_acceptance.py`) | approved |
| CLS-001 | `clinical/classification-rules.md`, `clinical-rules.yaml`, `monitoring-rules.yaml`, `comorbidity-constraints.yaml` | approved (values: see CLS-001-REF) |
| CLS-001-REF | `clinical/references.md` | draft — 9 items secondary-2026, rest to verify / judgement |
| AI-001 | `ai/langgraph-spec.md`, `ai/prompts/*.md` | approved |
| GR-001 | `ai/guardrails-spec.md`, `ai/banned-terms.yaml`, `ai/fallback-content.yaml` | approved |
| EV-001 | `ai/evaluation-spec.md`, `quality/golden-cases.jsonl`, `quality/golden_oracle.py` | approved |
| DM-001 | `data/data-model.md`, `data/schemas/*.schema.json` | approved |
| ARC-001 | `architecture/architecture.md`, `architecture/openapi.yaml` | approved |
| ARC-002 | `architecture/deployment.md` | approved |
| ADR 0001–0004 | `architecture/adr/` | accepted |
| TS-001 | `quality/test-strategy.md` | approved |
| Q-08 | `quality/accessibility-checklist.md` | approved |
| AC-EVIDENCE | `quality/acceptance-evidence.md` | approved |
| DEMO-001 | `quality/demo-script.md` | approved |
| CI | `.github/workflows/ci.yml` | added (runs once the repo is on GitHub) |

# Traceability matrix

Code and test columns are filled in as each phase lands.

| Requirement | Spec | Acceptance | Code | Tests |
| --- | --- | --- | --- | --- |
| F1.1 HbA1c input | FS-F1, DM-001 | AC-1 | `app/schemas/`, `rules/classify.py` | `test_rules.py::test_out_of_range_hba1c_raises` |
| F1.2 Classification | FS-F1, CLS-001 §2 | AC-1 | `rules/classify.py` | `test_rules.py::test_classification_boundaries`, golden |
| F1.3 Eligibility | FS-F1, CLS-001 §1, GR-001 G1 | AC-2 | `rules/eligibility.py` | `test_rules.py::test_eligibility_order`, golden G04/G12–G14 |
| F1.4 Urgent flag | FS-F1, CLS-001 §3 | AC-3 | `rules/classify.py` | `test_rules.py::test_urgent_threshold`, golden G05/G11 |
| F2.1–F2.5 Data collection | FS-F2, DM-001 | — (schema tests) | `app/schemas/` (generated), `api/routes.py` (spec validation), BMI in `rules/metrics.py` | `test_rules.py::test_bmi_*`, `test_api.py::test_comorbidity_none_is_exclusive` |
| F3.1 Calorie target | FS-F3, CLS-001 §5 | AC-6 | `rules/metrics.py` | `test_rules.py::test_calorie_*`, golden |
| F3.2 Diet plan | FS-F3, AI-001, GR-001 | AC-4, AC-6, AC-7 | `graph/nodes.py::write_diet_plan`, `safety/checks.py` (S3, S4) | `test_safety.py`, `test_graph.py` |
| F3.3 Lifestyle plan | FS-F3, AI-001, GR-001 | AC-7 | `graph/nodes.py::write_lifestyle_plan` | `test_graph.py` |
| F3.4 Comorbidity adjustments | FS-F3, CLS-001 §8 | AC-5 | `rules/risk.py` | golden (constraint_checks, doctor questions) |
| F4.1–F4.2 Monitoring | FS-F4, CLS-001 §7 | AC-5, golden | `rules/monitoring.py` | `test_rules.py::test_monitoring_*`, golden |
| F5.1 Report | FS-F5, DM-001 | AC-7 | `report/assemble.py`, `api/routes.py`, `db/`; UI `frontend/components/report/report-view.tsx`, `frontend/app/report/[id]/` | `test_api.py` (all 20 golden cases schema-valid); browser journeys 2026-10-10 |
| F5.2 PDF | FS-F5 | AC-8 | `report/pdf.py`, `report/templates/report.html`, `api/routes.py`; UI `report-actions.tsx` | `test_report_outputs.py::test_pdf_*` (content, 10 sections, urgent first, < 5 s) |
| F5.3 Share link | FS-F5, DM-001 | AC-8 | `db/repository.py`, `api/routes.py`; UI `report-actions.tsx`, `frontend/app/share/[token]/` | `test_report_outputs.py::test_share_*`, `test_revoked_*`, `test_expired_*`; browser 2026-10-10 |
| F5.4 Feedback | FS-F5 | — | `api/routes.py`; UI `frontend/app/report/[id]/feedback.tsx` | `test_report_outputs.py::test_*feedback*`; browser 2026-10-10 |
| NFR-1 Latency | PRD-001 | AC-9 | — | `evals/run_golden.py` (live, Tier 3) |
| GR-001 Safety check, retry, fallback | GR-001 §3–4 | AC-7 | `graph/nodes.py::safety_check`, `safety/` | `test_safety.py`, `test_graph.py` |
| UJ-1 Main journey | UJ-001, FS-F1, FS-F2 | AC-1, AC-3 | `frontend/app/page.tsx`, `frontend/app/assess/step-{1,2,3}/`, `frontend/lib/form-store.ts` | Browser: Meena (G02), Joseph (G05) 2026-10-10 |
| UJ-2 Ineligible exit | UJ-001, GR-001 G1 | AC-2 | `frontend/app/assess/referral/` | Browser: Priya (G04) 2026-10-10 |
| UJ-3 Urgent flag | UJ-001, FS-F1 | AC-3 | step-1 result card, `report-view.tsx` urgent banner | Browser: Joseph (G05) 2026-10-10 |
| NFR-4 Accessibility (basics) | PRD-001 | — | `frontend/components/ui.tsx`, `frontend/lib/focus-error.ts` | Q-08 checklist 2026-10-10: 14/15 pass (screen-reader pass recommended) |
| NFR-6 Rate limit | PRD-001 | — | `api/ratelimit.py` | `test_api.py::test_rate_limit_ten_per_minute` |
| NFR-7 Tracing | AI-001 §7 | AC-2 (0 LLM spans) | `tracing.py`, `assessment.py` | `test_graph.py::test_ineligible_makes_no_llm_calls`; manual Phoenix check 2026-10-10 |
