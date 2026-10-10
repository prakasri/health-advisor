# Build from the repo root so specs/ is baked into the image:
#   docker build -f backend/Dockerfile -t health-advisor-api .
# Secrets are never in the image (.dockerignore excludes .env files); they arrive as environment
# variables at runtime (Cloud Run: Secret Manager).
FROM python:3.12-slim

# Pango + friends for WeasyPrint PDF rendering
RUN apt-get update && apt-get install -y --no-install-recommends \
        libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /srv/backend
COPY backend/pyproject.toml backend/uv.lock ./
RUN uv sync --frozen --no-dev --no-install-project

COPY backend/ ./
COPY specs/ /srv/specs/

RUN useradd --system --uid 10001 app && chown -R app /srv
USER app

ENV SPECS_DIR=/srv/specs PATH="/srv/backend/.venv/bin:$PATH" PORT=8000
EXPOSE 8000
# Cloud Run sets $PORT. Proxy headers let the rate limiter see the client IP behind Google's front end.
CMD ["sh", "-c", "exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT} --proxy-headers --forwarded-allow-ips='*'"]
