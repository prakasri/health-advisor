---
id: FS-F3
title: F3 Recommendation engine
status: draft
version: 1.0.0
depends_on: [CLS-001, AI-001, GR-001]
implements: [F3.1, F3.2, F3.3, F3.4]
last_reviewed: 2026-10-10
---

# FS-F3 Recommendation engine

## F3.1 Calorie target (rules)
CLS-001 §5. Integer kcal, multiple of 50. Shown in the Dietary Guidance section header and passed to the
diet prompt as a fixed value.

## F3.2 Diet plan (LLM — `write_diet_plan`)
Output `DietPlan` (`report.schema.json#/$defs/DietPlan`):

| Field | Requirement |
| --- | --- |
| breakfast, lunch, dinner | 2–3 options each, each with name, description, portion |
| snacks | 2–4 options |
| foods_to_eat / foods_to_avoid | ≥ 5 each, region-appropriate |
| portion_guidance | Plate method in household measures |
| hydration | Plain guidance; respect any fluid caution from constraints |
| based_on | Inputs that shaped the plan |

Must satisfy GR-001 S2–S5 (no banned terms, diet preference, numbers, constraint checks).

## F3.3 Lifestyle plan (LLM — `write_lifestyle_plan`)
Output `LifestylePlan`: exercise (≥ 2), walking_goal (specific minutes/days/start point),
weight_management (matches BMI category), sleep, stress (≥ 2 techniques), behaviour_change (≥ 2;
includes smoking cessation if current smoker, alcohol reduction if regular), based_on.

## F3.4 Comorbidity adjustments (rules → LLM)
For each comorbidity, `comorbidity-constraints.yaml` supplies diet and lifestyle lines (hard
constraints in the prompts, listed verbatim under "Your plan follows these rules" in the report), a
required doctor question, and an optional machine check.

## Report mapping
| Report section | Source |
| --- | --- |
| Dietary Guidance | `calorie_target` + `diet_constraints` (rules) + `DietPlan` (LLM) |
| Lifestyle Guidance | `LifestylePlan` (LLM) |
| Preventative Actions | `Narrative.preventive_actions` (LLM) |
