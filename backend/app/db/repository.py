"""Persistence for DM-001. All writes for one assessment happen in a single transaction."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.assessment import AssessmentOutcome
from app.db.models import Assessment, Report
from app.schemas import AssessmentInput


def save_assessment(session: Session, inp: AssessmentInput, outcome: AssessmentOutcome) -> Report:
    rules = outcome.rules
    assessment = Assessment(
        id=outcome.assessment_id,
        hba1c=inp.hba1c,
        eligible=rules is not None,
        classification=rules.classification.classification if rules else None,
        urgent=rules.classification.urgent if rules else False,
        bmi=rules.bmi if rules else None,
        calorie_target=rules.calorie_target if rules else None,
        inputs=inp.model_dump(mode="json"),
        status="complete",
    )
    meta = outcome.report.meta
    report = Report(
        assessment_id=outcome.assessment_id,
        kind=outcome.report.kind,
        content=outcome.report.model_dump(mode="json", exclude_none=True),
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
