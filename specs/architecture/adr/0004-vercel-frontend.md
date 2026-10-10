# ADR 0004 — Vercel for frontend hosting, AWS for backend

- Status: accepted · Date: 2026-10-10

## Context
Amplify works but Vercel builds Next.js with zero configuration and gives preview URLs, saving time.

## Decision
Host `frontend/` on Vercel. The browser calls `/api/*` on the Vercel domain; a Next.js rewrite proxies
to the EC2 API (`API_ORIGIN`). No CORS is needed. All processing and storage stay on AWS ap-south-1.

## Consequences
+ Faster deploys, previews, single domain for share links. − Health inputs transit Vercel servers
(US-hosted by default, not stored) — data-residency item for V2. − Two platforms to manage.
Fallback: serve Next.js from the EC2 host.
