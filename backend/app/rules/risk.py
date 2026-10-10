"""Risk factors and comorbidity constraints (CLS-001 §6, §8; F3.4)."""

from dataclasses import dataclass, field

from app.rules.loader import clinical_rules, comorbidity_constraints
from app.rules.metrics import uses_asian_cutoffs
from app.schemas import AssessmentInput, RiskFactor


@dataclass(frozen=True)
class RiskProfile:
    risk_factors: list[RiskFactor]
    diet_constraints: list[str] = field(default_factory=list)
    lifestyle_constraints: list[str] = field(default_factory=list)
    doctor_questions_required: list[str] = field(default_factory=list)
    constraint_checks: list[str] = field(default_factory=list)


def comorbidities(inp: AssessmentInput) -> list[str]:
    return [c for c in inp.comorbidities if c != "none"]


def comorbidity_label(condition: str) -> str:
    return comorbidity_constraints()[condition]["label"]


def _triggered_by(rule_id: str, inp: AssessmentInput, classification: str, bmi: float) -> str:
    match rule_id:
        case "hba1c_prediabetes" | "hba1c_diabetes":
            return f"hba1c={inp.hba1c}% ({classification} range)"
        case "overweight" | "obesity":
            cutoffs = "asian" if uses_asian_cutoffs(inp.region) else "standard"
            return f"bmi={bmi} ({cutoffs} cut-offs)"
        case "family_history":
            return "family_history=yes"
        case "inactivity":
            return f"activity={inp.activity}"
        case "smoking":
            return f"smoking={inp.smoking}"
        case "alcohol":
            return f"alcohol={inp.alcohol}"
        case "age_45_plus":
            return f"age={inp.age}"
    raise KeyError(rule_id)


def _matches(when: dict, inp: AssessmentInput, classification: str, bmi_category: str) -> bool:
    for key, expected in when.items():
        match key:
            case "classification":
                ok = classification in expected
            case "bmi_category":
                ok = bmi_category in expected
            case "family_history":
                ok = inp.family_history is expected
            case "activity" | "smoking" | "alcohol":
                ok = getattr(inp, key) in expected
            case "age_min":
                ok = inp.age >= expected
            case _:
                raise ValueError(f"Unknown risk-factor key {key!r} in clinical-rules.yaml")
        if not ok:
            return False
    return True


def assess_risk(
    inp: AssessmentInput, classification: str, bmi: float, bmi_category: str
) -> RiskProfile:
    factors: list[RiskFactor] = []
    for rule in clinical_rules()["risk_factors"]:
        if rule["when"].get("any_comorbidity"):
            for condition in comorbidities(inp):
                factors.append(
                    RiskFactor(
                        id=f"comorbidity:{condition}",
                        label=rule["label"].format(condition=comorbidity_label(condition)),
                        triggered_by=f"comorbidities includes {condition}",
                    )
                )
        elif _matches(rule["when"], inp, classification, bmi_category):
            factors.append(
                RiskFactor(
                    id=rule["id"],
                    label=rule["label"],
                    triggered_by=_triggered_by(rule["id"], inp, classification, bmi),
                )
            )

    constraints = comorbidity_constraints()
    selected = [constraints[c] for c in comorbidities(inp)]
    return RiskProfile(
        risk_factors=factors,
        diet_constraints=[line for c in selected for line in c["diet"]],
        lifestyle_constraints=[line for c in selected for line in c["lifestyle"]],
        doctor_questions_required=[c["doctor_question"] for c in selected],
        constraint_checks=sorted({c["check"] for c in selected if "check" in c}),
    )
