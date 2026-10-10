#!/usr/bin/env bash
# ARC-002: remove the Google Cloud resources created by deploy/cloud-run.sh (stops all GCP charges).
# Neon, Phoenix Cloud and Vercel are separate accounts — delete those projects in their dashboards.
#
# Usage (from the repo root):  PROJECT_ID=health-advisor-511214 ./deploy/teardown-gcp.sh
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?set PROJECT_ID}"
REGION="${REGION:-asia-south1}"
SERVICE="${SERVICE:-health-advisor-api}"
REPO="${REPO:-health-advisor}"
gc() { gcloud --project "$PROJECT_ID" --quiet "$@"; }

echo "This deletes in project $PROJECT_ID:"
echo "  - Cloud Run service $SERVICE ($REGION)"
echo "  - Artifact Registry repository $REPO (all images)"
echo "  - Secrets health-advisor-database-url, -anthropic-api-key, -phoenix-api-key"
read -r -p "Type the project ID to confirm: " answer
[[ "$answer" == "$PROJECT_ID" ]] || { echo "Cancelled."; exit 1; }

gc run services delete "$SERVICE" --region "$REGION" || true
gc artifacts repositories delete "$REPO" --location "$REGION" || true
for s in health-advisor-database-url health-advisor-anthropic-api-key health-advisor-phoenix-api-key; do
  gc secrets delete "$s" || true
done

echo "Done. Also consider:"
echo "  - Vercel: delete project 'health-advisor' (vercel project rm health-advisor)"
echo "  - Neon and Phoenix Cloud: delete the projects/spaces in their dashboards"
echo "  - Anthropic: revoke the production API key"
echo "  - Optionally delete the whole GCP project: gcloud projects delete $PROJECT_ID"
