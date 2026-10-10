"""Graph nodes (AI-001 §3). Rule nodes are thin wrappers over app.rules; LLM nodes never raise."""

from app.config import settings
from app.graph.state import AssessmentState
from app.llm import LLMError, get_llm, prompt, prompt_version
from app.report.assemble import full_report, referral_report
from app.rules import (
    MonitoringContext,
    RuleResult,
    assess_risk,
    bmi,
    bmi_category,
    calorie_target,
    classify,
    comorbidities,
    exit_reason,
    plan_monitoring,
)
from app.rules.classify import round_half_up
from app.rules.risk import comorbidity_label
from app.safety.checks import CheckContext, run_rule_checks
from app.safety.fallback import fallback_diet, fallback_lifestyle, fallback_narrative
from app.safety.judge import run_judge
from app.schemas import DietPlan, LifestylePlan, Narrative

MAX_ATTEMPTS = 2


# --- rule nodes -----------------------------------------------------------------------------
def validate_input(state: AssessmentState) -> dict:
    inp = state["inputs"]
    return {
        "exit_reason": exit_reason(inp.age, inp.pregnant, inp.type1_diabetes),
        "llm_enabled": get_llm() is not None,
        "attempts": 0,
        "llm_errors": [],
    }


def classify_node(state: AssessmentState) -> dict:
    return {"classification": classify(state["inputs"].hba1c)}


def compute_metrics(state: AssessmentState) -> dict:
    inp = state["inputs"]
    value = bmi(inp.height_cm, inp.weight_kg)
    category = bmi_category(value, inp.region)
    kcal = calorie_target(inp.gender, inp.age, inp.height_cm, inp.weight_kg, inp.activity, category)
    return {"bmi": value, "bmi_category": category, "calorie_target": kcal}


def assess_risk_node(state: AssessmentState) -> dict:
    risk = assess_risk(
        state["inputs"], state["classification"].classification, state["bmi"], state["bmi_category"]
    )
    return {"risk": risk}


def plan_monitoring_node(state: AssessmentState) -> dict:
    inp, cls = state["inputs"], state["classification"]
    ctx = MonitoringContext(
        classification=cls.classification,
        urgent=cls.urgent,
        comorbidities=frozenset(comorbidities(inp)),
        smoking=inp.smoking,
        alcohol=inp.alcohol,
        diet=inp.diet,
        family_history=inp.family_history,
        age=inp.age,
        bmi_category=state["bmi_category"],
    )
    return {"monitoring": plan_monitoring(ctx)}


# --- LLM nodes ------------------------------------------------------------------------------
def _profile(state: AssessmentState) -> dict:
    inp = state["inputs"]
    return {
        "age": inp.age,
        "gender": inp.gender,
        "diet": inp.diet,
        "region": inp.region,
        "activity": inp.activity,
        "smoking": inp.smoking,
        "alcohol": inp.alcohol,
        "classification_label": state["classification"].label,
        "bmi": state["bmi"],
        "bmi_category": state["bmi_category"],
        "comorbidities": [comorbidity_label(c) for c in comorbidities(inp)],
    }


def _feedback(state: AssessmentState) -> dict:
    failures = state.get("safety_failures") or []
    return {"fix_these_problems": [f.detail for f in failures]} if failures else {}


def _generate(node: str, payload: dict, output):
    try:
        return get_llm().generate(
            node=node,
            system=prompt(node).system,
            payload=payload,
            output=output,
            effort=settings.llm_effort_writer,
        ), []
    except LLMError as exc:
        return None, [str(exc)]


def write_diet_plan(state: AssessmentState) -> dict:
    payload = {
        "profile": _profile(state),
        "calorie_target": state["calorie_target"],
        "constraints": state["risk"].diet_constraints,
        **_feedback(state),
    }
    plan, errors = _generate("write_diet_plan", payload, DietPlan)
    return {"diet_plan": plan, "llm_errors": errors}


def write_lifestyle_plan(state: AssessmentState) -> dict:
    payload = {
        "profile": _profile(state),
        "risk_factors": [f.label for f in state["risk"].risk_factors],
        "constraints": state["risk"].lifestyle_constraints,
        **_feedback(state),
    }
    plan, errors = _generate("write_lifestyle_plan", payload, LifestylePlan)
    return {"lifestyle_plan": plan, "llm_errors": errors}


def write_narrative(state: AssessmentState) -> dict:
    cls = state["classification"]
    lifestyle = state.get("lifestyle_plan")
    payload = {
        "profile": _profile(state),
        "status": {
            "hba1c": cls.hba1c,
            "classification_label": cls.label,
            "urgent": cls.urgent,
            "bmi": state["bmi"],
            "bmi_category": state["bmi_category"],
        },
        "risk_factors": [f.label for f in state["risk"].risk_factors],
        "monitoring": [{"name": m.name, "highlighted": m.highlighted} for m in state["monitoring"]],
        "diet_summary": {
            "calorie_target": state["calorie_target"],
            "constraints": state["risk"].diet_constraints,
        },
        "lifestyle_summary": {"walking_goal": lifestyle.walking_goal if lifestyle else None},
        "required_questions": state["risk"].doctor_questions_required,
        **_feedback(state),
    }
    narrative, errors = _generate("write_narrative", payload, Narrative)
    return {"narrative": narrative, "llm_errors": errors}


def safety_check(state: AssessmentState) -> dict:
    inp, cls, risk = state["inputs"], state["classification"], state["risk"]
    ctx = CheckContext(
        diet=inp.diet,
        calorie_target=state["calorie_target"],
        hba1c=cls.hba1c,
        bmi=state["bmi"],
        comorbidity_count=len(comorbidities(inp)),
        constraint_checks=risk.constraint_checks,
    )
    diet, lifestyle, narrative = (
        state.get("diet_plan"),
        state.get("lifestyle_plan"),
        state.get("narrative"),
    )
    failures = run_rule_checks(diet, lifestyle, narrative, ctx)
    if not failures:
        failures = run_judge(
            get_llm(),
            profile=_profile(state),
            constraints=risk.diet_constraints + risk.lifestyle_constraints,
            diet=diet,
            lifestyle=lifestyle,
            narrative=narrative,
        )
    return {
        "attempts": state["attempts"] + 1,
        "safety_passed": not failures,
        "safety_failures": failures,
    }


# --- output nodes ---------------------------------------------------------------------------
def ineligible_exit(state: AssessmentState) -> dict:
    inp = state["inputs"]
    report = referral_report(state["assessment_id"], state["exit_reason"], round_half_up(inp.hba1c))
    return {"report": report, "safety_passed": True}


def assemble_report(state: AssessmentState) -> dict:
    if "report" in state:  # referral already built by ineligible_exit
        return {}
    inp = state["inputs"]
    rules = RuleResult(
        classification=state["classification"],
        bmi=state["bmi"],
        bmi_category=state["bmi_category"],
        calorie_target=state["calorie_target"],
        risk=state["risk"],
        monitoring=state["monitoring"],
    )
    use_llm = state.get("llm_enabled") and state.get("safety_passed")
    if use_llm:
        diet, lifestyle, narrative = state["diet_plan"], state["lifestyle_plan"], state["narrative"]
    else:
        diet = fallback_diet(inp, rules)
        lifestyle = fallback_lifestyle(inp, rules)
        narrative = fallback_narrative(inp, rules)
    llm_ran = bool(state.get("llm_enabled"))
    report = full_report(
        state["assessment_id"],
        rules,
        diet,
        lifestyle,
        narrative,
        model_id=get_llm().model_id if llm_ran else None,
        prompt_version=prompt_version() if llm_ran else None,
        used_fallback=not use_llm,
    )
    return {"report": report, "safety_passed": bool(use_llm) or not llm_ran}
