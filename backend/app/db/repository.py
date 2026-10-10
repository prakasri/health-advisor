"""Persistence for DM-001. All writes for one assessment happen in a single transaction."""

import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy.orm import Session

from app.assessment import AssessmentOutcome
from app.db.models import Assessment, Feedback, Report, ShareLink
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


# --- F5.3 share links ---------------------------------------------------------------------
def create_share_link(session: Session, report_id: UUID, days: int) -> ShareLink:
    link = ShareLink(
        token=secrets.token_urlsafe(32),
        report_id=report_id,
        expires_at=datetime.now(UTC) + timedelta(days=days),
    )
    session.add(link)
    session.commit()
    return link


def get_active_share(session: Session, token: str) -> ShareLink | None:
    """A link is usable when it exists, is not revoked and has not expired (DM-001)."""
    link = session.get(ShareLink, token)
    if link is None or link.revoked or link.expires_at <= datetime.now(UTC):
        return None
    return link


def record_share_view(session: Session, link: ShareLink) -> None:
    link.view_count += 1
    session.commit()


def revoke_share(session: Session, token: str) -> bool:
    link = session.get(ShareLink, token)
    if link is None or link.revoked:
        return False
    link.revoked = True
    session.commit()
    return True


# --- F5.4 feedback ------------------------------------------------------------------------
def add_feedback(session: Session, report_id: UUID, helpful: bool, comment: str | None) -> None:
    session.add(Feedback(report_id=report_id, helpful=helpful, comment=comment or None))
    session.commit()
