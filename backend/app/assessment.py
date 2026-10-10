"""Runs one assessment end to end. Phase 3: rules + fallback text; Phase 4 swaps in the graph."""

from dataclasses import dataclass
from uuid import UUID, uuid4

from app.report.assemble import full_report, referral_report
from app.rules import RuleResult, evaluate, exit_reason
from app.rules.classify import round_half_up
from app.safety.fallback import fallback_diet, fallback_lifestyle, fallback_narrative
from app.schemas import AssessmentInput, Report


@dataclass(frozen=True)
class AssessmentOutcome:
    assessment_id: UUID
    report: Report
    rules: RuleResult | None  # None when ineligible
    safety_passed: bool


def run_assessment(inp: AssessmentInput) -> AssessmentOutcome:
    assessment_id = uuid4()
    reason = exit_reason(inp.age, inp.pregnant, inp.type1_diabetes)
    if reason is not None:
        report = referral_report(assessment_id, reason, round_half_up(inp.hba1c))
        return AssessmentOutcome(assessment_id, report, None, safety_passed=True)

    rules = evaluate(inp)
    report = full_report(
        assessment_id,
        rules,
        fallback_diet(inp, rules),
        fallback_lifestyle(inp, rules),
        fallback_narrative(inp, rules),
        model_id=None,
        prompt_version=None,
        used_fallback=True,
    )
    return AssessmentOutcome(assessment_id, report, rules, safety_passed=True)
