# GENERATED from specs/data/schemas/report.schema.json — do not edit. Run scripts/gen_schemas.sh.

from __future__ import annotations

from uuid import UUID
from pydantic import AwareDatetime, BaseModel, ConfigDict, Field
from typing import Annotated, Literal


class Meta(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    assessment_id: UUID
    created_at: AwareDatetime
    rules_version: str
    model_id: str | None = None
    prompt_version: str | None = None
    used_fallback: bool | None = False


class Referral(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    reason: Literal["under_18", "pregnant", "type1"]
    message: str
    hba1c: float


class Status(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    hba1c: float
    classification: Literal["normal", "prediabetes", "diabetes"]
    label: Annotated[str, Field(description="e.g. 'In the prediabetes range'")]
    explanation: str
    urgent: bool
    bmi: float
    bmi_category: Literal["underweight", "normal", "overweight", "obese"]
    urgent_message: Annotated[
        str | None, Field(description="Shown first in report and PDF when urgent (F1.4).")
    ] = None


class RiskFactor(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    id: str
    label: str
    triggered_by: Annotated[str, Field(description="Input that triggered it, e.g. 'bmi=27.4'")]


class ComorbidityNote(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    condition: str
    note: str


class MealOption(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    name: str
    description: str
    portion: str


class DietPlan(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    breakfast: Annotated[list[MealOption], Field(max_length=3, min_length=2)]
    lunch: Annotated[list[MealOption], Field(max_length=3, min_length=2)]
    dinner: Annotated[list[MealOption], Field(max_length=3, min_length=2)]
    snacks: Annotated[list[MealOption], Field(max_length=4, min_length=2)]
    foods_to_eat: Annotated[list[str], Field(min_length=5)]
    foods_to_avoid: Annotated[list[str], Field(min_length=5)]
    portion_guidance: str
    hydration: str
    based_on: Annotated[list[str], Field(min_length=1)]


class DietSection(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    calorie_target: int
    constraints: list[str]
    plan: DietPlan


class LifestylePlan(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    exercise: Annotated[list[str], Field(min_length=2)]
    walking_goal: str
    weight_management: str
    sleep: str
    stress: Annotated[list[str], Field(min_length=2)]
    behaviour_change: Annotated[list[str], Field(min_length=2)]
    based_on: Annotated[list[str], Field(min_length=1)]


class Narrative(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    summary: str
    comorbidity_assessment: list[ComorbidityNote]
    preventive_actions: Annotated[list[str], Field(min_length=3)]
    doctor_questions: Annotated[list[str], Field(max_length=8, min_length=3)]


class MonitoringItem(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    id: str
    name: str
    kind: Literal["lab", "screening"]
    why: str
    frequency: str
    risk_indicators: list[str]
    highlighted: bool


class Report(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    kind: Literal["full", "referral"]
    meta: Meta
    disclaimer: Annotated[str, Field(min_length=1)]
    referral: Referral | None = None
    status: Status | None = None
    summary: str | None = None
    risk_factors: list[RiskFactor] | None = None
    comorbidity_assessment: list[ComorbidityNote] | None = None
    diet: DietSection | None = None
    lifestyle: LifestylePlan | None = None
    monitoring: list[MonitoringItem] | None = None
    preventive_actions: Annotated[list[str] | None, Field(min_length=1)] = None
    doctor_questions: Annotated[list[str] | None, Field(min_length=3)] = None
    hba1c_caveat: str | None = None
