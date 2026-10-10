"""FS-F5 F5.2-F5.4 and AC-8 (report.feature): PDF download, share links, feedback."""

import io
import json
import time
from datetime import UTC, datetime, timedelta

import pytest
from pypdf import PdfReader
from sqlalchemy import select

from app.config import settings
from app.db.models import Feedback, ShareLink

CASES = {
    c["id"]: c
    for c in map(
        json.loads, (settings.specs_dir / "quality/golden-cases.jsonl").read_text().splitlines()
    )
}


@pytest.fixture
def report_id(client):
    return client.post("/api/assessments", json=CASES["G02"]["input"]).json()["report_id"]


def pdf_text(content: bytes) -> str:
    return "\n".join(page.extract_text() for page in PdfReader(io.BytesIO(content)).pages)


# --- F5.2 PDF (AC-8) --------------------------------------------------------------------------
def test_pdf_download(client, report_id):
    start = time.perf_counter()
    res = client.get(f"/api/reports/{report_id}/pdf")
    elapsed = time.perf_counter() - start
    assert res.status_code == 200
    assert res.headers["content-type"] == "application/pdf"
    assert res.headers["content-disposition"].startswith('attachment; filename="health-report-')
    assert res.headers["cache-control"] == "no-store"
    text = pdf_text(res.content)
    assert "Questions to Discuss with a Doctor" in text
    assert "not a medical diagnosis" in text
    assert "1,200 kcal" in text
    assert elapsed < 5


def test_pdf_has_all_ten_sections(client, report_id):
    text = pdf_text(client.get(f"/api/reports/{report_id}/pdf").content)
    for title in [
        "Overall Health Summary",
        "Diabetes Status",
        "Identified Risk Factors",
        "Comorbidity Assessment",
        "Dietary Guidance",
        "Lifestyle Guidance",
        "Monitoring Recommendations",
        "Preventative Actions",
        "Questions to Discuss with a Doctor",
        "Medical Disclaimer",
    ]:
        assert title in text, title


def test_urgent_pdf_leads_with_the_urgent_message(client):
    rid = client.post("/api/assessments", json=CASES["G05"]["input"]).json()["report_id"]
    text = pdf_text(client.get(f"/api/reports/{rid}/pdf").content)
    assert text.index("Please see a doctor soon") < text.index("Overall Health Summary")


def test_referral_pdf(client):
    rid = client.post("/api/assessments", json=CASES["G04"]["input"]).json()["report_id"]
    text = pdf_text(client.get(f"/api/reports/{rid}/pdf").content)
    assert "Please talk to your doctor" in text
    assert "6.0%" in text


def test_pdf_for_unknown_report_is_404(client):
    assert client.get("/api/reports/00000000-0000-0000-0000-000000000000/pdf").status_code == 404


# --- F5.3 share links (AC-8) ------------------------------------------------------------------
def test_share_link_opens_without_login_and_expires_in_30_days(client, report_id, db):
    res = client.post(f"/api/reports/{report_id}/share")
    assert res.status_code == 201
    body = res.json()
    assert body["url_path"] == f"/share/{body['token']}"
    assert len(body["token"]) >= 43  # 256-bit token
    expires = datetime.fromisoformat(body["expires_at"])
    assert abs((expires - datetime.now(UTC)) - timedelta(days=30)) < timedelta(minutes=1)

    shared = client.get(f"/api/share/{body['token']}")
    assert shared.status_code == 200
    assert shared.json()["report"]["kind"] == "full"
    link = db.get(ShareLink, body["token"])
    db.refresh(link)
    assert link.view_count == 1


def test_shared_pdf(client, report_id):
    token = client.post(f"/api/reports/{report_id}/share").json()["token"]
    res = client.get(f"/api/share/{token}/pdf")
    assert res.status_code == 200
    assert "Medical Disclaimer" in pdf_text(res.content)


def test_revoked_link_returns_404(client, report_id):
    token = client.post(f"/api/reports/{report_id}/share").json()["token"]
    assert client.delete(f"/api/share/{token}").status_code == 204
    assert client.get(f"/api/share/{token}").status_code == 404
    assert client.get(f"/api/share/{token}/pdf").status_code == 404
    assert client.delete(f"/api/share/{token}").status_code == 404  # already revoked


def test_expired_link_returns_404(client, report_id, db):
    token = client.post(f"/api/reports/{report_id}/share").json()["token"]
    link = db.get(ShareLink, token)
    link.expires_at = datetime.now(UTC) - timedelta(days=1)
    db.commit()
    assert client.get(f"/api/share/{token}").status_code == 404


def test_unknown_token_gives_same_404_as_revoked(client):
    res = client.get("/api/share/" + "x" * 43)
    assert res.status_code == 404
    assert res.json()["detail"] == "This link is no longer available"


def test_share_for_unknown_report_is_404(client):
    assert client.post("/api/reports/00000000-0000-0000-0000-000000000000/share").status_code == 404


# --- F5.4 feedback ----------------------------------------------------------------------------
def test_feedback_is_recorded(client, report_id, db):
    res = client.post(
        f"/api/reports/{report_id}/feedback", json={"helpful": True, "comment": "Clear"}
    )
    assert res.status_code == 201
    row = db.scalar(select(Feedback))
    assert row.helpful is True and row.comment == "Clear"


@pytest.mark.parametrize(
    "body",
    [
        {"helpful": True, "comment": "x" * 501},
        {"comment": "no rating"},
        {"helpful": True, "email": "a@b.c"},
    ],
)
def test_invalid_feedback_rejected(client, report_id, body):
    assert client.post(f"/api/reports/{report_id}/feedback", json=body).status_code == 422
