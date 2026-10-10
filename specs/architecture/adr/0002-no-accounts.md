# ADR 0002 — No user accounts in the MVP

- Status: accepted · Date: 2026-10-10

## Context
Two-day build; health data is sensitive; accounts bring auth, consent and DPDP/GDPR obligations.

## Decision
Anonymous assessments. No name, email, phone or IP stored. Reports are reached by UUID; share links
use 256-bit tokens with 30-day expiry. Data deleted after 90 days.

## Consequences
+ Small privacy surface, no auth work. − No history or progress tracking (V1); report URLs are bearer
links (accepted risk in VIS-001).
