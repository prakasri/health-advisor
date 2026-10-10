---
id: ARC-002
title: Deployment
status: approved
version: 2.0.0
depends_on: [ARC-001, ADR-0004, ADR-0005]
last_reviewed: 2026-10-10
---

# ARC-002 Deployment

Version 2 (ADR 0005): API on **Google Cloud Run** (Mumbai), database on **Neon**, traces on
**Phoenix Cloud**, frontend on **Vercel**. Version 1 (EC2 + RDS on AWS) is superseded; its
`deploy/docker-compose.yml` + `Caddyfile` remain as a self-hosting option.

| Component | Service | Configuration |
| --- | --- | --- |
| Frontend | Vercel (Hobby), project root `frontend/` | Env `API_ORIGIN=<Cloud Run URL>` (production) |
| API | Cloud Run service `health-advisor-api`, `asia-south1` | Image from Artifact Registry; 1 vCPU, 1 GiB; min 0, max 2 instances; concurrency 20; timeout 120 s; CPU boost |
| Build | Cloud Build (`deploy/cloudbuild.yaml`) | Builds `backend/Dockerfile` from the repo root; no local Docker needed |
| Database | Neon PostgreSQL (free tier), AWS `ap-south-1` | Pooled endpoint, `sslmode=require`; databases migrated with Alembic from the developer machine |
| Secrets | Google Secret Manager | `health-advisor-database-url`, `-anthropic-api-key`, `-phoenix-api-key`; mounted as env vars |
| Tracing | Arize Phoenix Cloud | `PHOENIX_COLLECTOR_ENDPOINT` + `PHOENIX_API_KEY`; project `health-advisor` |
| TLS | Built in (Cloud Run, Vercel) | — |

## Live (2026-10-10)
| What | URL |
| --- | --- |
| Web | https://health-advisor-eta.vercel.app |
| API | https://health-advisor-api-1099158459764.asia-south1.run.app |
| GCP project | `health-advisor-511214` |

Note: new GCP projects run Cloud Build as the default compute service account without build
permissions; `deploy/cloud-run.sh` grants it `roles/cloudbuild.builds.builder`.

## Deploy procedure
1. Put production values in `backend/.env.production` (git-ignored; see `deploy/cloud-run.sh` header).
2. Migrate: `cd backend && DATABASE_URL="<neon url>" uv run alembic upgrade head`.
3. API: `PROJECT_ID=<gcp project> ./deploy/cloud-run.sh` (enables APIs, stores secrets, builds, deploys,
   prints the URL and checks `/api/health`).
4. Frontend: Vercel project with root `frontend/`, `API_ORIGIN` = the Cloud Run URL; `vercel --prod`.
5. Smoke test: health, one AI report, PDF, share link, a trace in Phoenix Cloud.

## Environments
| Env | Frontend | API | DB | Traces |
| --- | --- | --- | --- | --- |
| local | localhost:3001 | localhost:8000 | local Postgres | local Phoenix :6006 |
| production | Vercel | Cloud Run | Neon | Phoenix Cloud |

## Not set up for the MVP
- 90-day retention job (would be a Cloud Scheduler call to a protected endpoint or a Cloud Run job).
- Staging API for Vercel preview deployments (previews without `API_ORIGIN` cannot reach an API).

## Cost (estimate; verify on each provider's pricing page)
Cloud Run, Cloud Build, Artifact Registry and Secret Manager stay within Google's free tiers at demo
traffic; Neon free tier; Phoenix Cloud free tier; Vercel Hobby free. Expected ≈ $0/month, plus
Anthropic usage per report (≈ $0.05–0.15).
