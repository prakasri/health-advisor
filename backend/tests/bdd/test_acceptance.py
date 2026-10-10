"""AC-001: the Gherkin files in specs/functional/acceptance run as tests (pytest-bdd).

The feature files are the specification; this module only binds their steps to the API, the
graph (with FakeLLM) and the safety checks. A failing scenario means the code no longer meets the
spec as written.
"""

import io
import json
import os
import time
from datetime import UTC, datetime, timedelta

import pytest
from jsonschema import Draft202012Validator
from pypdf import PdfReader
from pytest_bdd import given, parsers, scenarios, then, when

from app.config import settings
from app.db.models import ShareLink
from app.llm import set_llm
from app.rules import evaluate
from app.rules.risk import comorbidities
from app.safety.checks import CheckContext, run_rule_checks
from app.schemas import AssessmentInput
from tests.fakes import good_diet, good_lifestyle, good_narrative, scripted

FEATURES = settings.specs_dir / "functional/acceptance"
scenarios(str(FEATURES / "classification.feature"))
scenarios(str(FEATURES / "recommendations.feature"))
scenarios(str(FEATURES / "report.feature"))

CASES = {
    c["id"]: c
    for c in map(
        json.loads, (settings.specs_dir / "quality/golden-cases.jsonl").read_text().splitlines()
    )
}
REPORT_SCHEMA = Draft202012Validator(
    json.loads((settings.specs_dir / "data/schemas/report.schema.json").read_text())
)
ADULT = CASES["G03"]["input"]  # eligible adult; HbA1c varied per scenario
BANNED = "You have diabetes."


@pytest.fixture
def ctx():
    state: dict = {}
    yield state
    set_llm(None)


def _pdf_text(content: bytes) -> str:
    return "\n".join(p.extract_text() for p in PdfReader(io.BytesIO(content)).pages)


def _check_context(inp: AssessmentInput) -> CheckContext:
    r = evaluate(inp)
    return CheckContext(
        diet=inp.diet,
        calorie_target=r.calorie_target,
        hba1c=r.classification.hba1c,
        bmi=r.bmi,
        comorbidity_count=len(comorbidities(inp)),
        constraint_checks=r.risk.constraint_checks,
    )


# --- Given ------------------------------------------------------------------------------------
@given("an eligible adult")
def eligible_adult(ctx):
    ctx["input"] = dict(ADULT)


@given(parsers.parse('golden case "{case_id}"'))
def golden_case(ctx, case_id):
    ctx["case_id"] = case_id
    ctx["input"] = dict(CASES[case_id]["input"])
    ctx["inp"] = AssessmentInput.model_validate(ctx["input"])


@given(
    parsers.parse(
        'a user aged {age:d} who is pregnant "{pregnant}" and has type 1 diabetes "{type1}"'
    )
)
def ineligible_user(ctx, age, pregnant, type1):
    ctx["input"] = {
        **ADULT,
        "age": age,
        "gender": "female",
        "pregnant": pregnant == "yes",
        "type1_diabetes": type1 == "yes",
    }


@given(parsers.parse('the diet writer returns a plan containing "{food}"'))
def diet_plan_with_food(ctx, food):
    ctx["diet"] = good_diet(ctx["inp"], extra_meal=food)


@given(parsers.parse('the diet writer mentions "{text}"'))
def diet_plan_mentions(ctx, text):
    ctx["diet"] = good_diet(ctx["inp"]).model_copy(update={"hydration": f"Stay within {text}."})


@given(parsers.parse('the narrative writer returns a summary containing "{text}"'))
def narrative_with(ctx, text):
    ctx["narrative"] = good_narrative(ctx["inp"]).model_copy(update={"summary": text})


@given("every LLM writer returns a banned phrase")
def all_writers_banned(ctx):
    inp = ctx["inp"]
    ctx["llm"] = scripted(
        inp,
        write_diet_plan=lambda p, n: good_diet(inp).model_copy(update={"hydration": BANNED}),
        write_lifestyle_plan=lambda p, n: good_lifestyle(inp).model_copy(update={"sleep": BANNED}),
        write_narrative=lambda p, n: good_narrative(inp).model_copy(update={"summary": BANNED}),
    )


@given(
    parsers.parse('a completed assessment for golden case "{case_id}"'), target_fixture="report_id"
)
def completed_assessment(client, case_id):
    return client.post("/api/assessments", json=CASES[case_id]["input"]).json()["report_id"]


@given("I created a share link")
def created_share_link(ctx, client, report_id):
    ctx["token"] = client.post(f"/api/reports/{report_id}/share").json()["token"]


@given("a share link that expired yesterday")
def expired_share_link(ctx, client, report_id, db):
    token = client.post(f"/api/reports/{report_id}/share").json()["token"]
    link = db.get(ShareLink, token)
    link.expires_at = datetime.now(UTC) - timedelta(days=1)
    db.commit()
    ctx["token"] = token


# --- When -------------------------------------------------------------------------------------
@when(parsers.parse("they submit an HbA1c of {hba1c:g}"))
def submit_hba1c(ctx, client, hba1c):
    body = {k: ctx["input"][k] for k in ("age", "pregnant", "type1_diabetes")} | {"hba1c": hba1c}
    ctx["response"] = client.post("/api/classify", json=body)


@when(parsers.parse("an adult submits an HbA1c of {hba1c:g}"))
def adult_submits(ctx, client, hba1c):
    eligible_adult(ctx)
    submit_hba1c(ctx, client, hba1c)


@when("they complete an assessment")
def complete_assessment(ctx, client):
    ctx["llm"] = scripted(AssessmentInput.model_validate(ADULT))
    set_llm(ctx["llm"])
    ctx["report"] = client.post("/api/assessments", json=ctx["input"]).json()["report"]


@when("the assessment completes")
def assessment_completes(ctx, client):
    ctx.setdefault("llm", scripted(ctx["inp"]))
    set_llm(ctx["llm"])
    res = client.post("/api/assessments", json=ctx["input"])
    assert res.status_code == 201
    ctx["report"] = res.json()["report"]
    ctx["report_id"] = res.json()["report_id"]


@when("the safety check runs")
def safety_check_runs(ctx):
    inp = ctx["inp"]
    ctx["failures"] = run_rule_checks(
        ctx.get("diet", good_diet(inp)),
        ctx.get("lifestyle", good_lifestyle(inp)),
        ctx.get("narrative", good_narrative(inp)),
        _check_context(inp),
    )


@when("I request the PDF")
def request_pdf(ctx, client, report_id):
    start = time.perf_counter()
    ctx["response"] = client.get(f"/api/reports/{report_id}/pdf")
    ctx["seconds"] = time.perf_counter() - start


@when("I create a share link")
def create_share_link(ctx, client, report_id):
    ctx["share"] = client.post(f"/api/reports/{report_id}/share").json()


@when("I revoke it")
def revoke(ctx, client):
    assert client.delete(f"/api/share/{ctx['token']}").status_code == 204


@when("I open it")
def open_it(ctx, client):
    ctx["response"] = client.get(f"/api/share/{ctx['token']}")


@when("10 assessments run end to end against the live LLM")
def live_latency(ctx):
    pytest.skip("@live: run evals/run_golden.py (EV-001 Tier 3) — final run p95 25.2 s")


# --- Then -------------------------------------------------------------------------------------
@then(parsers.parse('the classification is "{classification}"'))
def classification_is(ctx, classification):
    assert ctx["response"].json()["classification"] == classification


@then(parsers.parse('the label says "{label}"'))
def label_says(ctx, label):
    assert ctx["response"].json()["label"] == label


@then(parsers.parse("the API responds with status {code:d}"))
def api_status(ctx, code):
    assert ctx["response"].status_code == code


@then(parsers.parse('the report kind is "referral" with reason "{reason}"'))
def referral_reason(ctx, reason):
    assert ctx["report"]["kind"] == "referral"
    assert ctx["report"]["referral"]["reason"] == reason


@then("no LLM call was made")
def no_llm_call(ctx):
    assert ctx["llm"].calls == []


@then(parsers.parse("urgent is {urgent}"))
def urgent_is(ctx, urgent):
    assert ctx["response"].json()["urgent"] is (urgent == "true")


@then("the report status is urgent")
def status_urgent(ctx):
    assert ctx["report"]["status"]["urgent"] is True


@then("the rendered report shows the urgent message before the summary")
def urgent_before_summary(ctx, client):
    text = _pdf_text(client.get(f"/api/reports/{ctx['report_id']}/pdf").content)
    assert text.index("Please see a doctor soon") < text.index("Overall Health Summary")


@then(parsers.parse('the check "{check}" fails'))
def check_fails(ctx, check):
    assert check in {f.check for f in ctx["failures"]}


@then(parsers.parse('the check "{check}" passes'))
def check_passes(ctx, check):
    assert check not in {f.check for f in ctx["failures"]}


@then("the diet constraints mention protein and potassium")
def constraints_protein_potassium(ctx):
    text = " ".join(ctx["report"]["diet"]["constraints"]).lower()
    assert "protein" in text and "potassium" in text


@then(parsers.parse('the doctor questions include "{word}"'))
def doctor_questions_include(ctx, word):
    assert any(word in q for q in ctx["report"]["doctor_questions"])


@then(parsers.parse('the monitoring includes "{item_id}"'))
def monitoring_includes(ctx, item_id):
    assert item_id in {m["id"] for m in ctx["report"]["monitoring"]}


@then(parsers.parse('the safety check includes "{check_id}"'))
def safety_check_includes(ctx, check_id):
    assert check_id in evaluate(ctx["inp"]).risk.constraint_checks


@then(parsers.parse("the report calorie target is {kcal:d}"))
def calorie_target_is(ctx, kcal):
    assert ctx["report"]["diet"]["calorie_target"] == kcal


@then("no LLM text mentions a different calorie number")
def no_other_calories(ctx):
    inp = ctx["inp"]
    r = ctx["report"]
    failures = run_rule_checks(
        good_diet(inp).model_validate(r["diet"]["plan"]),
        good_lifestyle(inp).model_validate(r["lifestyle"]),
        good_narrative(inp).model_validate(
            {k: r[k] for k in ("summary", "comorbidity_assessment", "preventive_actions")}
            | {"doctor_questions": r["doctor_questions"][:8]}
        ),
        _check_context(inp),
    )
    assert "S4" not in {f.check for f in failures}


@then(parsers.parse("the writers were called exactly {n:d} times each"))
def writers_called(ctx, n):
    for node in ("write_diet_plan", "write_lifestyle_plan", "write_narrative"):
        assert ctx["llm"].count(node) == n


@then("the report uses fallback content")
def uses_fallback(ctx):
    assert ctx["report"]["meta"]["used_fallback"] is True
    assert BANNED not in json.dumps(ctx["report"])


@then("the report still has all 10 sections")
def all_ten_sections(ctx):
    for key in (
        "summary",
        "status",
        "risk_factors",
        "comorbidity_assessment",
        "diet",
        "lifestyle",
        "monitoring",
        "preventive_actions",
        "doctor_questions",
        "disclaimer",
    ):
        assert key in ctx["report"], key


@then("the report validates against report.schema.json")
def report_valid(ctx):
    assert [e.message for e in REPORT_SCHEMA.iter_errors(ctx["report"])] == []


@then(parsers.parse("it has {required:d} required doctor questions plus at least {extra:d} more"))
def doctor_question_count(ctx, required, extra):
    required_qs = evaluate(ctx["inp"]).risk.doctor_questions_required
    assert len(required_qs) == required
    questions = ctx["report"]["doctor_questions"]
    assert questions[:required] == required_qs
    assert len(questions) >= required + extra


@then("it contains the disclaimer")
def has_disclaimer(ctx):
    assert "not a medical diagnosis" in ctx["report"]["disclaimer"]


@then(parsers.parse("the response is a PDF within {seconds:d} seconds"))
def pdf_within(ctx, seconds):
    assert ctx["response"].status_code == 200
    assert ctx["response"].headers["content-type"] == "application/pdf"
    assert ctx["seconds"] < seconds
    ctx["pdf_text"] = _pdf_text(ctx["response"].content)


@then(parsers.parse('the PDF text contains "{text}"'))
def pdf_contains(ctx, text):
    assert text in ctx["pdf_text"]


@then("the PDF text contains the disclaimer")
def pdf_has_disclaimer(ctx):
    assert "not a medical diagnosis" in ctx["pdf_text"]


@then("the link expires 30 days from now")
def expires_30_days(ctx):
    expires = datetime.fromisoformat(ctx["share"]["expires_at"])
    assert abs((expires - datetime.now(UTC)) - timedelta(days=30)) < timedelta(minutes=1)


@then("opening the link returns the report")
def opening_returns_report(ctx, client):
    res = client.get(f"/api/share/{ctx['share']['token']}")
    assert res.status_code == 200
    assert res.json()["report"]["kind"] == "full"


@then("opening the link returns 404")
def opening_returns_404(ctx, client):
    assert client.get(f"/api/share/{ctx['token']}").status_code == 404


@then(parsers.parse("the response is {code:d}"))
def response_is(ctx, code):
    assert ctx["response"].status_code == code


@then(parsers.parse("the 95th percentile duration is under {seconds:d} seconds"))
def p95_under(ctx, seconds):  # pragma: no cover - @live scenario is skipped in CI
    assert os.environ.get("LIVE_EVAL")
