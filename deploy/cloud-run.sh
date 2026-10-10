#!/usr/bin/env bash
# ARC-002 / ADR 0005: deploy the API to Google Cloud Run (asia-south1).
#
# Prerequisites: gcloud logged in, a project with billing enabled, and backend/.env.production
# (git-ignored) containing:
#   DATABASE_URL=postgresql+psycopg://...neon.tech/neondb?sslmode=require
#   ANTHROPIC_API_KEY=sk-ant-...
#   PHOENIX_COLLECTOR_ENDPOINT=https://app.phoenix.arize.com/s/<space>/v1/traces
#   PHOENIX_API_KEY=...
#
# Usage (from the repo root):  PROJECT_ID=my-project ./deploy/cloud-run.sh
# Re-running is safe: it updates secrets with new versions and redeploys.
set -euo pipefail

PROJECT_ID="${PROJECT_ID:?set PROJECT_ID}"
REGION="${REGION:-asia-south1}"
SERVICE="${SERVICE:-health-advisor-api}"
REPO="${REPO:-health-advisor}"
ENV_FILE="${ENV_FILE:-backend/.env.production}"
IMAGE="${REGION}-docker.pkg.dev/${PROJECT_ID}/${REPO}/api:$(git rev-parse --short HEAD)"
SECRETS=(DATABASE_URL ANTHROPIC_API_KEY PHOENIX_API_KEY)

gc() { gcloud --project "$PROJECT_ID" --quiet "$@"; }

[[ -f "$ENV_FILE" ]] || { echo "Missing $ENV_FILE"; exit 1; }
# Value of KEY from the env file, with surrounding quotes and whitespace removed.
value() {
  local v
  v="$(grep -E "^$1=" "$ENV_FILE" | head -1 | cut -d= -f2-)"
  v="${v#"${v%%[![:space:]]*}"}"; v="${v%"${v##*[![:space:]]}"}"
  [[ "$v" == \"*\" || "$v" == \'*\' ]] && v="${v:1:${#v}-2}"
  printf '%s' "$v"
}
for k in "${SECRETS[@]}" PHOENIX_COLLECTOR_ENDPOINT; do
  [[ -n "$(value "$k")" ]] || { echo "$k is empty in $ENV_FILE"; exit 1; }
done
PHOENIX_ENDPOINT="$(value PHOENIX_COLLECTOR_ENDPOINT)"
[[ "$PHOENIX_ENDPOINT" == https://* ]] || { echo "PHOENIX_COLLECTOR_ENDPOINT must be an https:// URL (is it swapped with PHOENIX_API_KEY?)"; exit 1; }
[[ "$PHOENIX_ENDPOINT" == */v1/traces ]] || PHOENIX_ENDPOINT="${PHOENIX_ENDPOINT%/}/v1/traces"
[[ "$(value PHOENIX_API_KEY)" != https://* ]] || { echo "PHOENIX_API_KEY looks like a URL (swapped with PHOENIX_COLLECTOR_ENDPOINT?)"; exit 1; }

echo "==> Enabling APIs"
gc services enable run.googleapis.com cloudbuild.googleapis.com artifactregistry.googleapis.com secretmanager.googleapis.com

echo "==> Artifact Registry repository"
gc artifacts repositories describe "$REPO" --location "$REGION" >/dev/null 2>&1 ||
  gc artifacts repositories create "$REPO" --repository-format docker --location "$REGION"

echo "==> Secrets (values are never printed)"
for k in "${SECRETS[@]}"; do
  name="health-advisor-$(echo "$k" | tr '[:upper:]_' '[:lower:]-')"
  gc secrets describe "$name" >/dev/null 2>&1 || gc secrets create "$name" --replication-policy automatic >/dev/null
  printf '%s' "$(value "$k")" | gc secrets versions add "$name" --data-file=- >/dev/null
  echo "    $name: new version stored"
done

echo "==> Granting the runtime service account access to the secrets"
SA="$(gc projects describe "$PROJECT_ID" --format='value(projectNumber)')-compute@developer.gserviceaccount.com"
for k in "${SECRETS[@]}"; do
  name="health-advisor-$(echo "$k" | tr '[:upper:]_' '[:lower:]-')"
  gc secrets add-iam-policy-binding "$name" --member "serviceAccount:$SA" --role roles/secretmanager.secretAccessor >/dev/null
done

echo "==> Letting Cloud Build use the default compute service account"
# Newer projects run builds as this account without granting it build permissions.
gc projects add-iam-policy-binding "$PROJECT_ID" --member "serviceAccount:$SA" \
  --role roles/cloudbuild.builds.builder --condition None >/dev/null

echo "==> Building $IMAGE (Cloud Build)"
gc builds submit . --config deploy/cloudbuild.yaml --substitutions "_IMAGE=$IMAGE"

echo "==> Deploying $SERVICE"
gc run deploy "$SERVICE" \
  --image "$IMAGE" \
  --region "$REGION" \
  --allow-unauthenticated \
  --port 8000 \
  --cpu 1 --memory 1Gi \
  --min-instances 0 --max-instances 2 \
  --concurrency 20 --timeout 120 \
  --cpu-boost \
  --set-env-vars "ENV=production,TRACING_ENABLED=true,PHOENIX_PROJECT=health-advisor,PHOENIX_COLLECTOR_ENDPOINT=$PHOENIX_ENDPOINT,LLM_MODEL=claude-sonnet-5" \
  --set-secrets "DATABASE_URL=health-advisor-database-url:latest,ANTHROPIC_API_KEY=health-advisor-anthropic-api-key:latest,PHOENIX_API_KEY=health-advisor-phoenix-api-key:latest"

URL="$(gc run services describe "$SERVICE" --region "$REGION" --format='value(status.url)')"
echo "==> Live at $URL"
curl -fsS "$URL/api/health" && echo
