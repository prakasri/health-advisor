---
id: DM-001
title: Data model
status: approved
version: 1.0.0
depends_on: [VIS-001]
implements: [F5.1, F5.3]
last_reviewed: 2026-10-10
---

# DM-001 Data model

PostgreSQL 16+. Four tables. User inputs and generated content are stored as JSONB validated against
the schemas in `schemas/`; columns exist only for values we filter or report on. **No personal
identifiers** (name, email, phone, IP address) are stored anywhere.

## Schemas (single source of truth)

| File | Used for |
| --- | --- |
| `schemas/assessment-input.schema.json` | API request body, `assessment.inputs`, generated Pydantic + TypeScript types |
| `schemas/report.schema.json` | `report.content`, API responses, PDF template, LLM structured outputs (`$defs`) |

Graph state is defined in AI-001 §2 (Python TypedDict composed of these models).

## Tables

```sql
CREATE TABLE assessment (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  hba1c           NUMERIC(3,1) NOT NULL CHECK (hba1c BETWEEN 3.0 AND 20.0),
  eligible        BOOLEAN NOT NULL,
  classification  TEXT CHECK (classification IN ('normal','prediabetes','diabetes')),  -- NULL if ineligible
  urgent          BOOLEAN NOT NULL DEFAULT false,
  bmi             NUMERIC(4,1),
  calorie_target  INT,
  inputs          JSONB NOT NULL,
  status          TEXT NOT NULL DEFAULT 'processing'
                  CHECK (status IN ('processing','complete','failed'))
);

CREATE TABLE report (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  assessment_id   UUID NOT NULL UNIQUE REFERENCES assessment(id) ON DELETE CASCADE,
  kind            TEXT NOT NULL CHECK (kind IN ('full','referral')),
  content         JSONB NOT NULL,
  safety_passed   BOOLEAN NOT NULL,
  used_fallback   BOOLEAN NOT NULL DEFAULT false,
  rules_version   TEXT NOT NULL,
  model_id        TEXT,             -- NULL for referral / no-LLM reports
  prompt_version  TEXT,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE share_link (
  token           TEXT PRIMARY KEY,                 -- secrets.token_urlsafe(32): 43 chars, 256 bits
  report_id       UUID NOT NULL REFERENCES report(id) ON DELETE CASCADE,
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at      TIMESTAMPTZ NOT NULL,             -- created_at + 30 days
  revoked         BOOLEAN NOT NULL DEFAULT false,
  view_count      INT NOT NULL DEFAULT 0
);

CREATE TABLE feedback (
  id              BIGSERIAL PRIMARY KEY,
  report_id       UUID NOT NULL REFERENCES report(id) ON DELETE CASCADE,
  helpful         BOOLEAN NOT NULL,
  comment         TEXT CHECK (length(comment) <= 500),
  created_at      TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX assessment_class_created_idx ON assessment (classification, created_at);
CREATE INDEX share_link_report_idx ON share_link (report_id);
```

Migrations: Alembic in `backend/app/db/migrations`. Models: SQLAlchemy 2 in `backend/app/db/models.py`.

## Rules

- A share link is valid when `revoked = false AND expires_at > now()`; otherwise the API returns 404
  (never 410, to avoid confirming a token existed).
- Report IDs are UUIDv4 and act as capability URLs for the owner's own browser session; the owner keeps
  them in the URL only. Anyone with a report ID can read it — acceptable for the MVP because no identity
  is stored (documented risk, VIS-001).
- Retention: a daily job deletes `assessment` rows older than 90 days (cascades to report, share_link,
  feedback).
- Reference data (rules, prompts, banned terms) lives in versioned YAML/Markdown in `specs/`, not in
  tables, for the MVP.
