"""AssessmentState (AI-001 §2)."""

import operator
from typing import Annotated, Literal, TypedDict
from uuid import UUID

from app.rules import Classification, RiskProfile
from app.safety.checks import Failure
from app.schemas import AssessmentInput, DietPlan, LifestylePlan, MonitoringItem, Narrative, Report


class AssessmentState(TypedDict, total=False):
    assessment_id: UUID
    inputs: AssessmentInput
    # rules
    exit_reason: Literal["under_18", "pregnant", "type1"] | None
    classification: Classification
    bmi: float
    bmi_category: Literal["underweight", "normal", "overweight", "obese"]
    calorie_target: int
    risk: RiskProfile
    monitoring: list[MonitoringItem]
    # LLM
    llm_enabled: bool
    diet_plan: DietPlan | None
    lifestyle_plan: LifestylePlan | None
    narrative: Narrative | None
    llm_errors: Annotated[list[str], operator.add]  # parallel writers append
    # safety
    attempts: int
    safety_passed: bool
    safety_failures: list[Failure]
    # output
    report: Report
