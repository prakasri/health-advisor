"""Deterministic clinical rules (CLS-001). Pure functions; never import graph, api or db here."""

from dataclasses import dataclass

from app.rules.classify import Classification, classify
from app.rules.eligibility import ExitReason, exit_reason, referral_message
from app.rules.metrics import BmiCategory, bmi, bmi_category, calorie_target
from app.rules.monitoring import MonitoringContext, plan_monitoring
from app.rules.risk import RiskProfile, assess_risk, comorbidities
from app.schemas import AssessmentInput, MonitoringItem


@dataclass(frozen=True)
class RuleResult:
    """Everything the rule nodes compute for an eligible user."""

    classification: Classification
    bmi: float
    bmi_category: BmiCategory
    calorie_target: int
    risk: RiskProfile
    monitoring: list[MonitoringItem]


def evaluate(inp: AssessmentInput) -> RuleResult:
    """Run all rules for an eligible user (caller checks eligibility first)."""
    cls = classify(inp.hba1c)
    bmi_value = bmi(inp.height_cm, inp.weight_kg)
    category = bmi_category(bmi_value, inp.region)
    kcal = calorie_target(inp.gender, inp.age, inp.height_cm, inp.weight_kg, inp.activity, category)
    risk = assess_risk(inp, cls.classification, bmi_value, category)
    monitoring = plan_monitoring(
        MonitoringContext(
            classification=cls.classification,
            urgent=cls.urgent,
            comorbidities=frozenset(comorbidities(inp)),
            smoking=inp.smoking,
            alcohol=inp.alcohol,
            diet=inp.diet,
            family_history=inp.family_history,
            age=inp.age,
            bmi_category=category,
        )
    )
    return RuleResult(cls, bmi_value, category, kcal, risk, monitoring)


__all__ = [
    "Classification",
    "ExitReason",
    "MonitoringContext",
    "RiskProfile",
    "RuleResult",
    "assess_risk",
    "bmi",
    "bmi_category",
    "calorie_target",
    "classify",
    "comorbidities",
    "evaluate",
    "exit_reason",
    "plan_monitoring",
    "referral_message",
]
