"""Persistence for DM-001. All writes for one assessment happen in a single transaction."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.assessment import AssessmentOutcome
from app.db.models import Assessment, Report
from app.schemas import AssessmentInput


def save_assessment(session: Session, inp: AssessmentInput, outcome: AssessmentOutcome) -> Report:
    content = outcome.report
    status = content.status  # None for referral reports
    assessment = Assessment(
        id=outcome.assessment_id,
        hba1c=inp.hba1c,
        eligible=content.kind == "full",
        classification=status.classification if status else None,
        urgent=status.urgent if status else False,
        bmi=status.bmi if status else None,
        calorie_target=content.diet.calorie_target if content.diet else None,
        inputs=inp.model_dump(mode="json"),
        status="complete",
    )
    meta = content.meta
    report = Report(
        assessment_id=outcome.assessment_id,
        kind=content.kind,
        content=content.model_dump(mode="json", exclude_none=True),
        safety_passed=outcome.safety_passed,
        used_fallback=bool(meta.used_fallback),
        rules_version=meta.rules_version,
        model_id=meta.model_id,
        prompt_version=meta.prompt_version,
    )
    session.add_all([assessment, report])
    session.commit()
    return report


def get_report(session: Session, report_id: UUID) -> Report | None:
    return session.get(Report, report_id)
