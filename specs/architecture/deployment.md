---
id: ARC-002
title: Deployment
status: draft
version: 1.0.0
depends_on: [ARC-001]
last_reviewed: 2026-10-10
---

# ARC-002 Deployment

Region **ap-south-1 (Mumbai)**. Frontend on Vercel; everything that processes or stores health data on AWS.

| Component | Service | Config |
| --- | --- | --- |
| Frontend | Vercel (Hobby), project root `frontend/` | Env `API_ORIGIN=https://<API_DOMAIN>` (production), staging API or unset (preview) |
| API + Phoenix + Caddy | EC2 t3.small, Amazon Linux 2023, Docker Compose (`deploy/`) | Elastic IP; security group 80/443 from anywhere, 22 from developer IP only |
| Database | RDS PostgreSQL 16, db.t4g.micro, 20 GB gp3, encrypted, private | SG allows 5432 only from the EC2 SG; databases `health_advisor`, `phoenix` |
| Secrets | SSM Parameter Store `/health-advisor/*` (SecureString) | EC2 instance role can read the path; boot script writes `deploy/.env` |
| TLS | Caddy automatic HTTPS | `API_DOMAIN` = Route 53 subdomain or `api.<eip-with-dashes>.sslip.io` |
| LLM | Anthropic API | Key in SSM |

## Deploy procedure (API)
1. `ssh ec2-user@<eip>`; `cd /srv/health-advisor && git pull`
2. `./deploy/write-env.sh` (reads SSM → `deploy/.env`)
3. `docker compose -f deploy/docker-compose.yml up -d --build`
4. `docker compose exec api alembic upgrade head`
5. Smoke: `curl https://<API_DOMAIN>/api/health`

## Deploy procedure (frontend)
Push to `main` → Vercel production build. Pull requests → preview builds.

## Environments
| Env | Frontend | API | DB |
| --- | --- | --- | --- |
| local | localhost:3001 | localhost:8000 | local Postgres `health_advisor` |
| production | Vercel prod domain | `https://<API_DOMAIN>` | RDS |

(Staging API is optional for the MVP; previews without `API_ORIGIN` show a "preview — API disabled" notice.)

## Cost (estimate, verify in the AWS calculator)
EC2 t3.small + EIP + RDS db.t4g.micro + 20 GB storage ≈ USD 25–35/month; Vercel Hobby free.
