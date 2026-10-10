"""GR-001 J1: LLM safety judge, run only after the rule checks pass."""

from pydantic import BaseModel, ConfigDict

from app.config import settings
from app.llm import LLMClient, LLMError, prompt
from app.safety.checks import Failure
from app.schemas import DietPlan, LifestylePlan, Narrative


class JudgeVerdict(BaseModel):
    model_config = ConfigDict(extra="forbid")

    passed: bool
    problems: list[str]


def run_judge(
    llm: LLMClient,
    *,
    profile: dict,
    constraints: list[str],
    diet: DietPlan,
    lifestyle: LifestylePlan,
    narrative: Narrative,
) -> list[Failure]:
    payload = {
        "profile": profile,
        "constraints": constraints,
        "diet_plan": diet.model_dump(),
        "lifestyle_plan": lifestyle.model_dump(),
        "narrative": narrative.model_dump(),
    }
    try:
        verdict = llm.generate(
            node="safety_check",
            system=prompt("safety_check").system,
            payload=payload,
            output=JudgeVerdict,
            effort=settings.llm_effort_judge,
        )
    except LLMError as exc:
        # Fail closed: an unreviewed plan is never shown.
        return [Failure("J1", f"judge unavailable: {exc}")]
    if verdict.passed:
        return []
    return [Failure("J1", p) for p in verdict.problems] or [Failure("J1", "judge rejected")]
