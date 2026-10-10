"""ARC-001 contract tests: openapi.yaml paths, status codes, schema-valid bodies."""

import json
from uuid import UUID

import pytest
import yaml
from jsonschema import Draft202012Validator
from sqlalchemy import select

from app.api.ratelimit import limiter
from app.config import settings
from app.db.models import Assessment, Report
from app.main import app

SPECS = settings.specs_dir
REPORT_SCHEMA = Draft202012Validator(
    json.loads((SPECS / "data/schemas/report.schema.json").read_text())
)
CASES = {
    c["id"]: c
    for c in map(json.loads, (SPECS / "quality/golden-cases.jsonl").read_text().splitlines())
}
STEP1 = dict(hba1c=6.2, age=40, pregnant=False, type1_diabetes=False)
LATER_PHASES = {  # contract paths built in Phase 7 (PLAN-001)
    ("get", "/api/reports/{report_id}/pdf"),
    ("post", "/api/reports/{report_id}/share"),
    ("get", "/api/share/{token}"),
    ("delete", "/api/share/{token}"),
    ("get", "/api/share/{token}/pdf"),
    ("post", "/api/reports/{report_id}/feedback"),
}


def assert_valid_report(report: dict) -> None:
    errors = [e.message for e in REPORT_SCHEMA.iter_errors(report)]
    assert errors == []


def test_every_contract_path_is_implemented_or_scheduled():
    spec = yaml.safe_load((SPECS / "architecture/openapi.yaml").read_text())
    contract = {(m, p) for p, ops in spec["paths"].items() for m in ops}
    implemented = {(m, p) for p, ops in app.openapi()["paths"].items() for m in ops}
    missing = contract - implemented - LATER_PHASES
    undocumented = {(m, p) for m, p in implemented if p.startswith("/api")} - contract
    assert missing == set()
    assert undocumented == set()


def test_health(client):
    assert client.get("/api/health").json()["status"] == "ok"


# --- /api/classify ----------------------------------------------------------------------
def test_classify_eligible(client):
    body = client.post("/api/classify", json={**STEP1, "hba1c": 6.45}).json()
    assert body["eligible"] is True
    assert body["classification"] == "diabetes"
    assert body["hba1c"] == 6.5
    assert body["label"] == "In the diabetes range"
    assert body["urgent"] is False


def test_classify_urgent(client):
    body = client.post("/api/classify", json={**STEP1, "hba1c": 10.0}).json()
    assert body["urgent"] is True
    assert body["urgent_message"]


def test_classify_ineligible_has_no_classification(client):
    body = client.post("/api/classify", json={**STEP1, "pregnant": True}).json()
    assert body["eligible"] is False
    assert body["exit_reason"] == "pregnant"
    assert body["referral_message"]
    assert "classification" not in body


@pytest.mark.parametrize("hba1c", [2.9, 20.1])
def test_classify_rejects_out_of_range(client, hba1c):
    assert client.post("/api/classify", json={**STEP1, "hba1c": hba1c}).status_code == 422


def test_classify_rejects_unknown_fields(client):
    assert client.post("/api/classify", json={**STEP1, "name": "x"}).status_code == 422


# --- /api/assessments -------------------------------------------------------------------
def test_full_assessment_is_persisted_and_schema_valid(client, db):
    response = client.post("/api/assessments", json=CASES["G02"]["input"])
    assert response.status_code == 201
    body = response.json()
    report = body["report"]
    assert_valid_report(report)
    assert report["kind"] == "full"
    assert report["diet"]["calorie_target"] == CASES["G02"]["expected"]["calorie_target"]
    assert report["disclaimer"]

    row = db.scalar(select(Assessment).where(Assessment.id == UUID(body["assessment_id"])))
    assert row.status == "complete"
    assert row.classification == "diabetes"
    assert db.get(Report, UUID(body["report_id"])).kind == "full"


@pytest.mark.parametrize("case_id", ["G04", "G12", "G13", "G14"])
def test_ineligible_cases_get_referral(client, case_id):
    report = client.post("/api/assessments", json=CASES[case_id]["input"]).json()["report"]
    assert_valid_report(report)
    assert report["kind"] == "referral"
    assert report["referral"]["reason"] == CASES[case_id]["expected"]["exit_reason"]
    assert "status" not in report


@pytest.mark.parametrize("case", list(CASES.values()), ids=list(CASES))
def test_every_golden_case_returns_a_valid_report(client, case):
    response = client.post("/api/assessments", json=case["input"])
    assert response.status_code == 201
    assert_valid_report(response.json()["report"])


def test_comorbidity_none_is_exclusive(client):
    body = {**CASES["G02"]["input"], "comorbidities": ["none", "obesity"]}
    assert client.post("/api/assessments", json=body).status_code == 422


def test_out_of_range_height_rejected(client):
    body = {**CASES["G02"]["input"], "height_cm": 90}
    assert client.post("/api/assessments", json=body).status_code == 422


def test_comorbidity_questions_come_first(client):
    report = client.post("/api/assessments", json=CASES["G19"]["input"]).json()["report"]
    assert "nephrologist" in report["doctor_questions"][0]


# --- /api/reports/{id} ------------------------------------------------------------------
def test_get_report_round_trip(client):
    created = client.post("/api/assessments", json=CASES["G01"]["input"]).json()
    fetched = client.get(f"/api/reports/{created['report_id']}").json()
    assert fetched["report"] == created["report"]


def test_get_unknown_report_404(client):
    assert client.get("/api/reports/00000000-0000-0000-0000-000000000000").status_code == 404


def test_get_report_bad_uuid_422(client):
    assert client.get("/api/reports/not-a-uuid").status_code == 422


# --- NFR-6 rate limit -------------------------------------------------------------------
def test_rate_limit_ten_per_minute(client):
    limiter.enabled = True
    codes = [
        client.post("/api/assessments", json=CASES["G03"]["input"]).status_code for _ in range(11)
    ]
    assert codes[:10] == [201] * 10
    assert codes[10] == 429
