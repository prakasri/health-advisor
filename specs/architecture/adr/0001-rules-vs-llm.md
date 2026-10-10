# ADR 0001 — Deterministic rules for clinical facts, LLM only for personalised text

- Status: accepted · Date: 2026-10-10

## Context
The product classifies HbA1c, computes BMI and calorie targets, and recommends tests. These have
exact, guideline-defined answers. LLMs can drift, hallucinate numbers and are hard to test exactly.

## Decision
Classification, eligibility, urgent flag, BMI, calorie target, risk factors, monitoring and
comorbidity constraints are Python functions reading versioned YAML (CLS-001). The LLM only writes diet,
lifestyle and narrative text, receives rule outputs as read-only facts, and is checked afterwards (GR-001).

## Consequences
+ Exact, unit-testable clinical behaviour; explainable outputs; lower cost (3 LLM calls).
+ Clear responsible-AI story. − Rule tables need manual maintenance and clinical verification.
