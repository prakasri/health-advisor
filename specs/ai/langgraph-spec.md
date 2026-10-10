---
id: AI-001
title: LangGraph assessment graph
status: draft
version: 1.0.0
depends_on: [CLS-001, GR-001, DM-001]
implements: [F1.2, F3.1, F3.2, F3.3, F3.4, F4.1, F4.2, F5.1]
last_reviewed: 2026-10-10
---

# AI-001 LangGraph assessment graph

One graph, `assessment_graph`, compiled once at API start-up and invoked synchronously per
`POST /api/assessments`. No checkpointer (runs < 30 s, no human-in-the-loop).

## 1. Model

| Setting | Value |
| --- | --- |
| Provider | Anthropic API via `langchain-anthropic` (ADR 0003) |
| Model | `claude-sonnet-5` (env `LLM_MODEL`) for writers and judge |
| Structured output | `ChatAnthropic.with_structured_output(<PydanticModel>)` (tool use) |
| Temperature | 0.4 writers, 0 judge |
| Max output tokens | 2,000 diet, 1,200 lifestyle, 1,200 narrative, 400 judge |
| Timeout | 45 s per call; 1 automatic transport retry |

## 2. State (`app/graph/state.py`)

```python
class AssessmentState(TypedDict, total=False):
    assessment_id: str
    inputs: AssessmentInput                 # assessment-input.schema.json
    eligible: bool
    exit_reason: Literal["under_18", "pregnant", "type1"] | None
    classification: Literal["normal", "prediabetes", "diabetes"]
    urgent: bool
    bmi: float
    bmi_category: Literal["underweight", "normal", "overweight", "obese"]
    calorie_target: int
    risk_factors: list[RiskFactor]
    diet_constraints: list[str]
    lifestyle_constraints: list[str]
    doctor_questions_required: list[str]    # from comorbidity-constraints.yaml
    constraint_checks: list[str]            # e.g. ["no_high_protein"]
    monitoring: list[MonitoringItem]
    diet_plan: DietPlan | None
    lifestyle_plan: LifestylePlan | None
    narrative: Narrative | None
    safety: SafetyResult | None
    safety_feedback: list[str]              # failures fed back on retry
    attempts: int                           # LLM generation attempts, max 2
    report: Report
```

Pydantic models for `AssessmentInput`, `Report` and its `$defs` are generated from
`specs/data/schemas/*.schema.json` (datamodel-code-generator) into `app/schemas.py`.

## 3. Nodes

| # | Node | Kind | Reads → writes | Spec |
| --- | --- | --- | --- | --- |
| 1 | `validate_input` | rules | inputs → eligible, exit_reason | CLS-001 §1 |
| 2 | `classify` | rules | inputs.hba1c → classification, urgent | CLS-001 §2–3 |
| 3 | `compute_metrics` | rules | inputs → bmi, bmi_category, calorie_target | CLS-001 §4–5 |
| 4 | `assess_risk` | rules | inputs, classification, bmi_category → risk_factors, diet_constraints, lifestyle_constraints, doctor_questions_required, constraint_checks | CLS-001 §6, §8 |
| 5 | `plan_monitoring` | rules | classification, urgent, inputs, bmi_category → monitoring | CLS-001 §7 |
| 6 | `write_diet_plan` | LLM | profile, calorie_target, diet_constraints, safety_feedback → diet_plan | `prompts/diet_plan.v1.md` |
| 7 | `write_lifestyle_plan` | LLM | profile, risk_factors, lifestyle_constraints, safety_feedback → lifestyle_plan | `prompts/lifestyle_plan.v1.md` |
| 8 | `write_narrative` | LLM | all rule outputs + diet_plan + lifestyle_plan → narrative | `prompts/narrative.v1.md` |
| 9 | `safety_check` | rules + LLM judge | diet_plan, lifestyle_plan, narrative → safety, safety_feedback, attempts | GR-001 §3 |
| 10 | `assemble_report` | code | state → report (fallback text if safety failed twice) | DM-001, GR-001 §4 |
| 11 | `ineligible_exit` | code | exit_reason → report (kind=referral) | GR-001 G1 |

"profile" = age, gender, diet, region, activity, smoking, alcohol, comorbidity labels, classification
label, BMI and category. No assessment ID or other identifier is sent to the model.

## 4. Edges

```
START → validate_input
validate_input ─(eligible)→ classify ─(not eligible)→ ineligible_exit → assemble_report
classify → compute_metrics → assess_risk → plan_monitoring
plan_monitoring → [write_diet_plan ‖ write_lifestyle_plan]       # parallel fan-out
[write_diet_plan, write_lifestyle_plan] → write_narrative          # fan-in (waits for both)
write_narrative → safety_check
safety_check ─(passed)→ assemble_report
safety_check ─(failed, attempts < 2)→ [write_diet_plan ‖ write_lifestyle_plan]
safety_check ─(failed, attempts = 2)→ assemble_report               # uses fallback
assemble_report → END
```

Note: `ineligible_exit` runs before `classify`; the referral report still records the HbA1c value
but no classification label is shown (the user is told to discuss the value with their doctor).

## 5. Error handling

| Failure | Behaviour |
| --- | --- |
| LLM timeout / API error / no API key | Node catches, leaves its output `None`; `safety_check` fails S1; after attempt 2 → fallback. With no API key, skip straight to fallback (`attempts = 2`) so local dev works. |
| Structured output invalid | Same as above |
| Rule node exception | Propagates → HTTP 500, assessment `status = failed` (rules are deterministic; this is a bug) |

## 6. Prompt management

- One file per prompt in `specs/ai/prompts/<name>.v<N>.md` with front-matter (`id`, `version`,
  `node`, `output_schema`). The file body is the system prompt; the user message is the JSON payload
  described in the file.
- Loaded at start-up; the combined version string (e.g. `diet_plan.v1+lifestyle_plan.v1+narrative.v1+safety_judge.v1`)
  is stored in `report.meta.prompt_version`.
- Any wording change = new version file + golden-case run (EV-001).

## 7. Tracing (Phoenix)

- `phoenix.otel.register(project_name="health-advisor", endpoint=PHOENIX_COLLECTOR_ENDPOINT)` +
  `LangChainInstrumentor().instrument()` at start-up.
- One trace per graph run; root span attributes: `assessment_id`, `classification`, `eligible`,
  `used_fallback`, `prompt_version`, `rules_version`.
- Rule nodes appear as chain spans; LLM nodes as LLM spans with token counts.
- Acceptance: an ineligible run has **0 LLM spans**.
