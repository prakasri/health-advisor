"""EV-001 Tier 1: the 20 golden cases must match the independent oracle exactly."""

import json

import pytest

from app.config import settings
from app.rules import evaluate, exit_reason
from app.schemas import AssessmentInput

CASES = [
    json.loads(line)
    for line in (settings.specs_dir / "quality/golden-cases.jsonl").read_text().splitlines()
]


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_golden_case(case):
    inp = AssessmentInput.model_validate(case["input"])
    expected = case["expected"]

    reason = exit_reason(inp.age, inp.pregnant, inp.type1_diabetes)
    assert (reason is None) is expected["eligible"]
    assert reason == expected["exit_reason"]
    if reason is not None:
        return

    result = evaluate(inp)
    actual = {
        "hba1c_rounded": result.classification.hba1c,
        "classification": result.classification.classification,
        "urgent": result.classification.urgent,
        "bmi": result.bmi,
        "bmi_category": result.bmi_category,
        "calorie_target": result.calorie_target,
        "risk_factor_ids": [f.id for f in result.risk.risk_factors],
        "monitoring_ids": sorted(m.id for m in result.monitoring),
        "constraint_checks": result.risk.constraint_checks,
        "required_doctor_question_count": len(result.risk.doctor_questions_required),
    }
    assert actual == {k: expected[k] for k in actual}


def test_all_twenty_cases_present():
    assert len(CASES) == 20
