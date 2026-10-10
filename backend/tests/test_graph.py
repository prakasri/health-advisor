"""EV-001 Tier 2: graph routing, parallel writers, retry and fallback (fake LLM)."""

import json

import pytest
from jsonschema import Draft202012Validator

from app.assessment import run_assessment
from app.config import settings
from app.llm import LLMError, set_llm
from app.safety.judge import JudgeVerdict
from app.schemas import AssessmentInput
from tests.fakes import fail, good_diet, good_lifestyle, good_narrative, scripted

SPECS = settings.specs_dir
CASES = {
    c["id"]: c
    for c in map(json.loads, (SPECS / "quality/golden-cases.jsonl").read_text().splitlines())
}
REPORT_SCHEMA = Draft202012Validator(
    json.loads((SPECS / "data/schemas/report.schema.json").read_text())
)
WRITERS = {"write_diet_plan", "write_lifestyle_plan", "write_narrative"}


def inp(case_id: str) -> AssessmentInput:
    return AssessmentInput.model_validate(CASES[case_id]["input"])


@pytest.fixture(autouse=True)
def _reset_llm():
    yield
    set_llm(None)


def run(case_id: str, llm=None):
    set_llm(llm)
    outcome = run_assessment(inp(case_id))
    report = outcome.report.model_dump(mode="json", exclude_none=True)
    assert [e.message for e in REPORT_SCHEMA.iter_errors(report)] == []
    return outcome


def test_happy_path_uses_llm_sections():
    llm = scripted(inp("G02"))
    outcome = run("G02", llm)
    report = outcome.report
    assert outcome.safety_passed
    assert report.meta.used_fallback is False
    assert report.meta.model_id == "fake-model"
    assert report.meta.prompt_version.startswith("diet_plan.v1+")
    assert report.diet.plan.lunch[0].name == "Moong dal with brown rice"
    assert report.diet.calorie_target == CASES["G02"]["expected"]["calorie_target"]
    assert sorted(llm.nodes()) == sorted([*WRITERS, "safety_check"])


def test_writers_run_in_parallel_before_narrative():
    llm = scripted(inp("G02"))
    run("G02", llm)
    order = llm.nodes()
    assert order.index("write_narrative") > max(
        order.index("write_diet_plan"), order.index("write_lifestyle_plan")
    )
    assert order[-1] == "safety_check"


def test_payload_carries_rule_facts_and_constraints():
    llm = scripted(inp("G19"))  # kidney disease, vegan
    run("G19", llm)
    diet_payload = next(c.payload for c in llm.calls if c.node == "write_diet_plan")
    assert diet_payload["calorie_target"] == CASES["G19"]["expected"]["calorie_target"]
    assert any("protein" in c for c in diet_payload["constraints"])
    assert diet_payload["profile"]["diet"] == "vegan"
    assert "assessment_id" not in json.dumps(diet_payload)  # GR-001 G6: no identifiers to the model


@pytest.mark.parametrize("case_id", ["G04", "G12", "G13", "G14"])
def test_ineligible_makes_no_llm_calls(case_id):
    llm = scripted(inp("G02"))
    outcome = run(case_id, llm)
    assert outcome.report.kind == "referral"
    assert llm.calls == []  # AC-2


def test_no_llm_configured_uses_fallback_without_calls():
    outcome = run("G02", None)
    assert outcome.report.meta.used_fallback is True
    assert outcome.report.meta.model_id is None
    assert outcome.safety_passed is True


def test_retry_with_feedback_then_pass():
    i = inp("G02")  # vegetarian
    llm = scripted(
        i,
        write_diet_plan=lambda p, n: good_diet(i, extra_meal="Chicken curry" if n == 1 else None),
    )
    outcome = run("G02", llm)
    assert outcome.safety_passed
    assert outcome.report.meta.used_fallback is False
    assert llm.count("write_diet_plan") == 2
    retry_payload = [c.payload for c in llm.calls if c.node == "write_diet_plan"][1]
    assert any("chicken" in p for p in retry_payload["fix_these_problems"])
    assert llm.count("safety_check") == 1  # judge only runs once rule checks pass


def test_two_failures_fall_back_to_standard_guidance():
    i = inp("G02")
    llm = scripted(
        i,
        write_narrative=lambda p, n: good_narrative(i).model_copy(
            update={"summary": "You have diabetes."}
        ),
    )
    outcome = run("G02", llm)
    assert outcome.safety_passed is False
    assert outcome.report.meta.used_fallback is True
    assert outcome.report.meta.model_id == "fake-model"  # the LLM did run; its output was rejected
    assert {n: llm.count(n) for n in WRITERS} == {n: 2 for n in WRITERS}
    assert "You have diabetes" not in outcome.report.summary


def test_llm_error_is_retried_then_recovers():
    i = inp("G03")
    llm = scripted(
        i,
        write_lifestyle_plan=lambda p, n: LLMError("timeout") if n == 1 else good_lifestyle(i),
    )
    outcome = run("G03", llm)
    assert outcome.safety_passed
    assert outcome.llm_errors == ["timeout"]
    assert llm.count("write_lifestyle_plan") == 2


def test_llm_down_falls_back():
    i = inp("G01")
    llm = scripted(i, write_diet_plan=fail(), write_lifestyle_plan=fail(), write_narrative=fail())
    outcome = run("G01", llm)
    assert outcome.report.meta.used_fallback is True
    assert llm.count("safety_check") == 0


def test_judge_rejection_triggers_retry():
    i = inp("G10")
    llm = scripted(
        i,
        safety_check=lambda p, n: JudgeVerdict(passed=n > 1, problems=["Unsafe exercise advice"]),
    )
    outcome = run("G10", llm)
    assert outcome.safety_passed
    assert llm.count("safety_check") == 2
    retry = [c.payload for c in llm.calls if c.node == "write_lifestyle_plan"][1]
    assert retry["fix_these_problems"] == ["Unsafe exercise advice"]


def test_judge_unavailable_fails_closed():
    i = inp("G10")
    llm = scripted(i, safety_check=fail("judge down"))
    outcome = run("G10", llm)
    assert outcome.safety_passed is False
    assert outcome.report.meta.used_fallback is True


def test_required_doctor_questions_lead_the_list():
    i = inp("G20")  # 8 comorbidities
    outcome = run("G20", scripted(i))
    questions = outcome.report.doctor_questions
    assert len(questions) >= 8 + 3
    assert "nephrologist" in " ".join(questions[:8])


def test_urgent_report_keeps_urgent_message():
    outcome = run("G05", scripted(inp("G05")))
    assert outcome.report.status.urgent is True
    assert outcome.report.status.urgent_message.startswith("Your HbA1c is 10% or higher")


@pytest.mark.parametrize("case_id", [c for c in CASES if CASES[c]["expected"]["eligible"]])
def test_every_eligible_golden_case_passes_with_safe_outputs(case_id):
    outcome = run(case_id, scripted(inp(case_id)))
    assert outcome.safety_passed, outcome
    assert outcome.report.meta.used_fallback is False


def test_attempts_reported():
    assert run("G02", scripted(inp("G02"))).attempts == 1
    assert run("G02", None).attempts == 0
