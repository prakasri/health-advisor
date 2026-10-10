# ADR 0005 — Google Cloud Run + Neon + Phoenix Cloud instead of AWS (supersedes ARC-002 v1 hosting)

- Status: accepted · Date: 2026-10-10

## Context
The AWS plan (EC2 + RDS, ≈ $35/month; Lightsail ≈ $7–12) costs money every hour for a demo with
very light traffic. AWS is not a course requirement. The app is already a single Docker image whose
only dependencies are PostgreSQL, the Anthropic API and an OTLP trace collector.

## Decision
- **API:** Google Cloud Run, region `asia-south1` (Mumbai), built remotely by Cloud Build from
  `backend/Dockerfile`; min 0 / max 2 instances, 1 vCPU, 1 GiB, CPU boost on cold start.
- **Database:** Neon serverless PostgreSQL (free tier), region AWS `ap-south-1`, pooled connection
  with TLS (`sslmode=require`). Migrations run from the developer machine with Alembic.
- **Tracing:** Arize Phoenix Cloud (hosted Phoenix), via the same OpenTelemetry setup plus an API key.
- **Secrets:** Google Secret Manager, injected as environment variables; never in the image
  (`.dockerignore`/`.gcloudignore` exclude `.env` files).
- **Frontend:** unchanged — Vercel, `/api/*` rewritten to the Cloud Run URL (ADR 0004).

## Consequences
+ ≈ $0/month at demo traffic (scale to zero, free tiers); HTTPS and logs built in; no server to patch.
+ Same container runs locally, in CI and in production.
− Cold start of a few seconds after idle (WeasyPrint warm-up runs at start-up).
− Rate limiting is per instance (max 2 instances caps the effect and the cost).
− The 90-day retention job needs Cloud Scheduler (not set up for the MVP; documented in ARC-002).
− Health data now leaves AWS: inputs pass through Vercel (US) and Google (Mumbai); the database
  stays in Mumbai (Neon on AWS ap-south-1).
