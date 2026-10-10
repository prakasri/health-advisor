"""GR-001 §4 rule-only fallback for the three LLM sections (specs/ai/fallback-content.yaml)."""

from functools import cache
from typing import Any

import yaml

from app.config import settings
from app.rules import RuleResult
from app.rules.risk import comorbidity_label
from app.schemas import AssessmentInput, ComorbidityNote, DietPlan, LifestylePlan, Narrative


@cache
def fallback_content() -> dict[str, Any]:
    with (settings.specs_dir / "ai/fallback-content.yaml").open(encoding="utf-8") as f:
        return yaml.safe_load(f)


@cache
def report_text() -> dict[str, Any]:
    with (settings.specs_dir / "ai/report-text.yaml").open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def fallback_diet(inp: AssessmentInput, rules: RuleResult) -> DietPlan:
    diet = fallback_content()["diet"]
    return DietPlan(
        **diet["meals"],
        foods_to_eat=diet["foods_to_eat"]["all"] + diet["foods_to_eat"][inp.diet],
        foods_to_avoid=diet["foods_to_avoid"],
        portion_guidance=diet["portion_guidance"].strip(),
        hydration=diet["hydration"].strip(),
        based_on=["standard guidance", f"calorie target {rules.calorie_target:,} kcal"],
    )


def fallback_lifestyle(inp: AssessmentInput, rules: RuleResult) -> LifestylePlan:
    life = fallback_content()["lifestyle"]
    exercise = life["exercise"] + rules.risk.lifestyle_constraints
    weight = (
        life["weight_management"]
        if rules.bmi_category in ("overweight", "obese")
        else "Your weight is not above the healthy range; focus on staying active and eating well."
    )
    return LifestylePlan(
        exercise=exercise,
        walking_goal=life["walking_goal"],
        weight_management=weight,
        sleep=life["sleep"],
        stress=life["stress"],
        behaviour_change=life["behaviour_change"],
        based_on=["standard guidance"],
    )


def fallback_narrative(inp: AssessmentInput, rules: RuleResult) -> Narrative:
    narrative = fallback_content()["narrative"]
    # Lower-case only the first letter so acronyms survive ("BMI in the obese range").
    factors = [
        f.label if f.label[1:2].isupper() else f.label[0].lower() + f.label[1:]
        for f in rules.risk.risk_factors
        if not f.id.startswith("hba1c")
    ]
    risk_sentence = f"Factors that raise your risk include {', '.join(factors)}." if factors else ""
    summary = narrative["summary_template"].format(
        hba1c=rules.classification.hba1c,
        label_lower=rules.classification.label[0].lower() + rules.classification.label[1:],
        risk_sentence=risk_sentence,
    )
    if rules.classification.urgent:
        summary = f"{rules.classification.urgent_message} {summary}"
    template = report_text()["comorbidity_fallback_note"].strip()
    return Narrative(
        summary=" ".join(summary.split()),
        comorbidity_assessment=[
            ComorbidityNote(
                condition=comorbidity_label(c), note=template.format(label=comorbidity_label(c))
            )
            for c in inp.comorbidities
            if c != "none"
        ],
        preventive_actions=narrative["preventive_actions"],
        doctor_questions=narrative["doctor_questions"],
    )
