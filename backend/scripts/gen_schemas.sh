#!/usr/bin/env bash
# Regenerate app/schemas/ from specs/data/schemas (DM-001). Run from backend/.
set -euo pipefail
mkdir -p app/schemas
for f in assessment-input report; do
  mod=${f//-/_}
  uv run datamodel-codegen --input ../specs/data/schemas/$f.schema.json --input-file-type jsonschema \
    --output app/schemas/$mod.py --output-model-type pydantic_v2.BaseModel \
    --target-python-version 3.12 --use-standard-collections --use-union-operator \
    --field-constraints --enum-field-as-literal all --use-title-as-name --disable-timestamp \
    --use-annotated --formatters ruff-format --custom-file-header \
    "# GENERATED from specs/data/schemas/$f.schema.json — do not edit. Run scripts/gen_schemas.sh." 2>/dev/null
done
cat > app/schemas/__init__.py <<'PY'
"""Pydantic models generated from specs/data/schemas (DM-001)."""
from app.schemas.assessment_input import AssessmentInput
from app.schemas.report import (
    ComorbidityNote,
    DietPlan,
    DietSection,
    LifestylePlan,
    MealOption,
    Meta,
    MonitoringItem,
    Narrative,
    Referral,
    Report,
    RiskFactor,
    Status,
)

__all__ = [
    "AssessmentInput", "ComorbidityNote", "DietPlan", "DietSection", "LifestylePlan", "MealOption",
    "Meta", "MonitoringItem", "Narrative", "Referral", "Report", "RiskFactor", "Status",
]
PY
