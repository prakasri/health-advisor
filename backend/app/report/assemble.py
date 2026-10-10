"""Builds the Report (FS-F5, report.schema.json) from rule outputs and written sections."""

from datetime import UTC, datetime
from uuid import UUID

from app.rules import ExitReason, RuleResult, referral_message
from app.rules.loader import rules_version
from app.safety.fallback import report_text
from app.schemas import (
    DietPlan,
    DietSection,
    LifestylePlan,
    Meta,
    Narrative,
    Referral,
    Report,
    Status,
)


def _meta(
    assessment_id: UUID,
    model_id: str | None = None,
    prompt_version: str | None = None,
    used_fallback: bool = False,
) -> Meta:
    return Meta(
        assessment_id=assessment_id,
        created_at=datetime.now(UTC),
        rules_version=rules_version(),
        model_id=model_id,
        prompt_version=prompt_version,
        used_fallback=used_fallback,
    )


def _dedupe(items: list[str]) -> list[str]:
    seen: set[str] = set()
    out = []
    for item in items:
        key = item.strip().lower()
        if key not in seen:
            seen.add(key)
            out.append(item)
    return out


def referral_report(assessment_id: UUID, reason: ExitReason, hba1c: float) -> Report:
    return Report(
        kind="referral",
        meta=_meta(assessment_id),
        disclaimer=report_text()["disclaimer"].strip(),
        referral=Referral(reason=reason, message=referral_message(reason), hba1c=hba1c),
    )


def full_report(
    assessment_id: UUID,
    rules: RuleResult,
    diet: DietPlan,
    lifestyle: LifestylePlan,
    narrative: Narrative,
    *,
    model_id: str | None,
    prompt_version: str | None,
    used_fallback: bool,
) -> Report:
    cls = rules.classification
    return Report(
        kind="full",
        meta=_meta(assessment_id, model_id, prompt_version, used_fallback),
        disclaimer=report_text()["disclaimer"].strip(),
        hba1c_caveat=report_text()["hba1c_caveat"].strip(),
        status=Status(
            hba1c=cls.hba1c,
            classification=cls.classification,
            label=cls.label,
            explanation=cls.explanation,
            urgent=cls.urgent,
            urgent_message=cls.urgent_message,
            bmi=rules.bmi,
            bmi_category=rules.bmi_category,
        ),
        summary=narrative.summary,
        risk_factors=rules.risk.risk_factors,
        comorbidity_assessment=narrative.comorbidity_assessment,
        diet=DietSection(
            calorie_target=rules.calorie_target,
            constraints=rules.risk.diet_constraints,
            plan=diet,
        ),
        lifestyle=lifestyle,
        monitoring=rules.monitoring,
        preventive_actions=narrative.preventive_actions,
        doctor_questions=_dedupe(rules.risk.doctor_questions_required + narrative.doctor_questions),
    )
