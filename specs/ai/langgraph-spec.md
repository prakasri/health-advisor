---
id: AI-001
title: LangGraph assessment graph
status: approved
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
| Provider | Official `anthropic` Python SDK called from the LangGraph nodes (ADR 0003). LangGraph orchestrates; it does not wrap the model. |
| Model | `claude-sonnet-5` (env `LLM_MODEL`) for writers and judge |
| Structured output | `client.messages.parse(..., output_format=<PydanticModel>)` → `response.parsed_output` (validated) |
| Thinking / effort | Adaptive thinking (Sonnet 5 default); `output_config.effort` = `low` for writers (latency budget NFR-1), `medium` for the judge — env `LLM_EFFORT_WRITER`, `LLM_EFFORT_JUDGE` |
| Sampling | No `temperature`/`top_p` — rejected by Claude Sonnet 5 |
| Max output tokens | 16,000 per call (non-streaming default; prevents truncated JSON) |
| Timeout / retries | 60 s per call; SDK retries 429/5xx/connection errors twice |
| Stop reasons | `refusal` or `max_tokens` → treated as a failed node output (GR-001 S1) |

## 2. State (`app/graph/state.py`)

```python
class AssessmentState(TypedDict, total=False):
    assessment_id: UUID
    inputs: AssessmentInput                      # assessment-input.schema.json
    # rules
    exit_reason: Literal["under_18", "pregnant", "type1"] | None
    classification: Classification               # rounded hba1c, band, label, explanation, urgent
    bmi: float
    bmi_category: Literal["underweight", "normal", "overweight", "obese"]
    calorie_target: int
    risk: RiskProfile                            # risk factors, diet/lifestyle constraints,
                                                 # required doctor questions, constraint checks
    monitoring: list[MonitoringItem]
    # LLM
    llm_enabled: bool                            # False when no API key → rule-only report
    diet_plan: DietPlan | None
    lifestyle_plan: LifestylePlan | None
    narrative: Narrative | None
    llm_errors: Annotated[list[str], operator.add]   # parallel writers append
    # safety
    attempts: int                                # generation rounds, max 2
    safety_passed: bool
    safety_failures: list[Failure]               # fed back to writers on retry
    # output
    report: Report
```

Pydantic models for `AssessmentInput`, `Report` and its `$defs` are generated from
`specs/data/schemas/*.schema.json` by `backend/scripts/gen_schemas.sh` into `app/schemas/`.

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
| 8 | `write_narrative` | LLM | rule outputs only (runs in parallel with 6–7, NFR-1) → narrative | `prompts/narrative.v2.md` |
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
plan_monitoring ─(llm_enabled)→ [write_diet_plan ‖ write_lifestyle_plan ‖ write_narrative]   # parallel
plan_monitoring ─(no LLM)→ assemble_report
[write_diet_plan, write_lifestyle_plan, write_narrative] → safety_check   # fan-in (waits for all 3)
safety_check ─(passed)→ assemble_report
safety_check ─(failed, attempts < 2)→ [all three writers, with failures as feedback]
safety_check ─(failed, attempts = 2)→ assemble_report               # uses fallback
assemble_report → END
```

Note: `ineligible_exit` runs before `classify`; the referral report still records the HbA1c value
but no classification label is shown (the user is told to discuss the value with their doctor).

## 5. Error handling

| Failure | Behaviour |
| --- | --- |
| LLM timeout / API error / refusal / truncation | `app/llm/client.py` raises `LLMError`; the node records it in `llm_errors` and leaves its output `None`; `safety_check` fails S1 → retry → fallback after attempt 2. |
| No API key | `llm_enabled = false`; `plan_monitoring` routes straight to `assemble_report` (rule-only report, 0 LLM calls) so local development works. |
| Judge unavailable | Fails closed: J1 failure → retry → fallback. |
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
