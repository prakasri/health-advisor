"""Runs one assessment end to end through the LangGraph assessment graph (AI-001)."""

from dataclasses import dataclass
from uuid import UUID, uuid4

from app.graph.graph import assessment_graph
from app.rules.loader import rules_version
from app.schemas import AssessmentInput, Report
from app.tracing import assessment_span


@dataclass(frozen=True)
class AssessmentOutcome:
    assessment_id: UUID
    report: Report
    safety_passed: bool
    llm_errors: list[str]
    attempts: int  # LLM generation rounds (0 = no LLM, 1 = passed first time, 2 = retried)


def run_assessment(inp: AssessmentInput) -> AssessmentOutcome:
    assessment_id = uuid4()
    with assessment_span(
        {"assessment_id": str(assessment_id), "rules_version": rules_version()}
    ) as span:
        state = assessment_graph().invoke({"assessment_id": assessment_id, "inputs": inp})
        report: Report = state["report"]
        if span is not None:
            span.set_attributes(
                {
                    "eligible": report.kind == "full",
                    "classification": report.status.classification if report.status else "none",
                    "used_fallback": bool(report.meta.used_fallback),
                    "prompt_version": report.meta.prompt_version or "none",
                    "attempts": state.get("attempts", 0),
                }
            )
    return AssessmentOutcome(
        assessment_id=assessment_id,
        report=report,
        safety_passed=state["safety_passed"],
        llm_errors=state.get("llm_errors", []),
        attempts=state.get("attempts", 0),
    )
