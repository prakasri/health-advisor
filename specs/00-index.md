---
id: INDEX
title: Specification index and traceability
status: draft
version: 1.0.0
last_reviewed: 2026-10-10
---

# Specification index

| ID | File | Status |
| --- | --- | --- |
| PLAN-001 | `00-build-plan.md` | approved |
| VIS-001 | `product/vision.md` | draft |
| PRD-001 | `product/prd.md` | draft |
| UJ-001 | `product/user-journeys.md` | draft |
| FS-F1..F5 | `functional/F1-classification.md` … `F5-report.md` | draft |
| AC-001 | `functional/acceptance/*.feature` | draft |
| CLS-001 | `clinical/classification-rules.md`, `clinical-rules.yaml`, `monitoring-rules.yaml`, `comorbidity-constraints.yaml` | draft — values to verify |
| CLS-001-REF | `clinical/references.md` | draft — sources to verify |
| AI-001 | `ai/langgraph-spec.md`, `ai/prompts/*.md` | draft |
| GR-001 | `ai/guardrails-spec.md`, `ai/banned-terms.yaml`, `ai/fallback-content.yaml` | draft |
| EV-001 | `ai/evaluation-spec.md`, `quality/golden-cases.jsonl`, `quality/golden_oracle.py` | draft |
| DM-001 | `data/data-model.md`, `data/schemas/*.schema.json` | draft |
| ARC-001 | `architecture/architecture.md`, `architecture/openapi.yaml` | draft |
| ARC-002 | `architecture/deployment.md` | draft |
| ADR 0001–0004 | `architecture/adr/` | accepted |
| TS-001 | `quality/test-strategy.md` | draft |

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
| F5.1 Report | FS-F5, DM-001 | AC-7 | `report/assemble.py`, `api/routes.py`, `db/` | `test_api.py` (all 20 golden cases schema-valid) |
| F5.2 PDF | FS-F5 | AC-8 | | |
| F5.3 Share link | FS-F5, DM-001 | AC-8 | | |
| F5.4 Feedback | FS-F5 | — | | |
| NFR-1 Latency | PRD-001 | AC-9 | — | `evals/run_golden.py` (live, Tier 3) |
| GR-001 Safety check, retry, fallback | GR-001 §3–4 | AC-7 | `graph/nodes.py::safety_check`, `safety/` | `test_safety.py`, `test_graph.py` |
| NFR-6 Rate limit | PRD-001 | — | `api/ratelimit.py` | `test_api.py::test_rate_limit_ten_per_minute` |
| NFR-7 Tracing | AI-001 §7 | AC-2 (0 LLM spans) | `tracing.py`, `assessment.py` | `test_graph.py::test_ineligible_makes_no_llm_calls`; manual Phoenix check 2026-10-10 |
