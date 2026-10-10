"""assessment_graph wiring (AI-001 §4)."""

from functools import cache

from langgraph.graph import END, START, StateGraph

from app.graph import nodes
from app.graph.state import AssessmentState

WRITERS = ["write_diet_plan", "write_lifestyle_plan"]


def _after_validate(state: AssessmentState) -> str:
    return "ineligible_exit" if state["exit_reason"] else "classify"


def _after_monitoring(state: AssessmentState) -> list[str] | str:
    # No LLM configured (e.g. no API key locally): go straight to the rule-only report.
    return WRITERS if state["llm_enabled"] else "assemble_report"


def _after_safety(state: AssessmentState) -> list[str] | str:
    if state["safety_passed"] or state["attempts"] >= nodes.MAX_ATTEMPTS:
        return "assemble_report"
    return WRITERS  # retry once with the failures as feedback


@cache
def assessment_graph():
    g = StateGraph(AssessmentState)
    g.add_node("validate_input", nodes.validate_input)
    g.add_node("classify", nodes.classify_node)
    g.add_node("compute_metrics", nodes.compute_metrics)
    g.add_node("assess_risk", nodes.assess_risk_node)
    g.add_node("plan_monitoring", nodes.plan_monitoring_node)
    g.add_node("write_diet_plan", nodes.write_diet_plan)
    g.add_node("write_lifestyle_plan", nodes.write_lifestyle_plan)
    g.add_node("write_narrative", nodes.write_narrative)
    g.add_node("safety_check", nodes.safety_check)
    g.add_node("ineligible_exit", nodes.ineligible_exit)
    g.add_node("assemble_report", nodes.assemble_report)

    g.add_edge(START, "validate_input")
    g.add_conditional_edges("validate_input", _after_validate, ["classify", "ineligible_exit"])
    g.add_edge("classify", "compute_metrics")
    g.add_edge("compute_metrics", "assess_risk")
    g.add_edge("assess_risk", "plan_monitoring")
    g.add_conditional_edges("plan_monitoring", _after_monitoring, [*WRITERS, "assemble_report"])
    g.add_edge(WRITERS, "write_narrative")  # fan-in: waits for both writers
    g.add_edge("write_narrative", "safety_check")
    g.add_conditional_edges("safety_check", _after_safety, [*WRITERS, "assemble_report"])
    g.add_edge("ineligible_exit", "assemble_report")
    g.add_edge("assemble_report", END)
    return g.compile()
