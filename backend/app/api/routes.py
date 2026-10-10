"""HTTP API (ARC-001, specs/architecture/openapi.yaml)."""

import json
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from jsonschema import Draft202012Validator
from sqlalchemy.orm import Session

from app.api.models import AssessmentResponse, ClassifyRequest, ClassifyResponse, ReportEnvelope
from app.api.ratelimit import limiter
from app.assessment import run_assessment
from app.config import settings
from app.db import repository
from app.db.session import get_session
from app.rules import classify, exit_reason, referral_message
from app.rules.classify import round_half_up
from app.schemas import AssessmentInput, Report

router = APIRouter(prefix="/api")
SessionDep = Annotated[Session, Depends(get_session)]

_input_validator = Draft202012Validator(
    json.loads((settings.specs_dir / "data/schemas/assessment-input.schema.json").read_text())
)


def _validate_against_spec(inp: AssessmentInput) -> None:
    """Enforce rules Pydantic can't express from the schema (e.g. 'none' is exclusive)."""
    errors = [
        {"loc": ["body", *e.absolute_path], "msg": e.message, "type": "schema"}
        for e in _input_validator.iter_errors(inp.model_dump(mode="json"))
    ]
    if errors:
        raise RequestValidationError(errors)


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "env": settings.env}


@router.post("/classify", response_model=ClassifyResponse, response_model_exclude_none=True)
def classify_step_one(body: ClassifyRequest) -> ClassifyResponse:
    reason = exit_reason(body.age, body.pregnant, body.type1_diabetes)
    if reason is not None:
        return ClassifyResponse(
            eligible=False,
            exit_reason=reason,
            referral_message=referral_message(reason),
            hba1c=round_half_up(body.hba1c),
        )
    result = classify(body.hba1c)
    return ClassifyResponse(
        eligible=True,
        hba1c=result.hba1c,
        classification=result.classification,
        label=result.label,
        explanation=result.explanation,
        urgent=result.urgent,
        urgent_message=result.urgent_message,
    )


@router.post(
    "/assessments",
    response_model=AssessmentResponse,
    response_model_exclude_none=True,
    status_code=status.HTTP_201_CREATED,
)
@limiter.limit("10/minute")
def create_assessment(
    request: Request, body: AssessmentInput, session: SessionDep
) -> AssessmentResponse:
    _validate_against_spec(body)
    outcome = run_assessment(body)
    row = repository.save_assessment(session, body, outcome)
    return AssessmentResponse(
        assessment_id=outcome.assessment_id, report_id=row.id, report=outcome.report
    )


@router.get("/reports/{report_id}", response_model=ReportEnvelope, response_model_exclude_none=True)
def get_report(report_id: UUID, session: SessionDep) -> ReportEnvelope:
    row = repository.get_report(session, report_id)
    if row is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Report not found")
    return ReportEnvelope(report_id=row.id, report=Report.model_validate(row.content))
