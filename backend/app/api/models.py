"""Request/response models defined inline in specs/architecture/openapi.yaml (ARC-001)."""

from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas import Report


class ClassifyRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    hba1c: Annotated[float, Field(ge=3.0, le=20.0)]
    age: Annotated[int, Field(ge=1, le=120)]
    pregnant: bool
    type1_diabetes: bool


class ClassifyResponse(BaseModel):
    eligible: bool
    exit_reason: Literal["under_18", "pregnant", "type1"] | None = None
    referral_message: str | None = None
    hba1c: float
    classification: Literal["normal", "prediabetes", "diabetes"] | None = None
    label: str | None = None
    explanation: str | None = None
    urgent: bool = False
    urgent_message: str | None = None


class AssessmentResponse(BaseModel):
    assessment_id: UUID
    report_id: UUID
    report: Report


class ReportEnvelope(BaseModel):
    report_id: UUID
    report: Report
