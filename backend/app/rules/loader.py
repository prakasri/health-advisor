"""Loads the versioned clinical rule files in specs/clinical (CLS-001)."""

from functools import cache
from pathlib import Path
from typing import Any

import yaml

from app.config import settings


def _load(relative: str) -> dict[str, Any]:
    path: Path = settings.specs_dir / relative
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f)


@cache
def clinical_rules() -> dict[str, Any]:
    return _load("clinical/clinical-rules.yaml")


@cache
def monitoring_rules() -> dict[str, Any]:
    return _load("clinical/monitoring-rules.yaml")


@cache
def comorbidity_constraints() -> dict[str, Any]:
    return _load("clinical/comorbidity-constraints.yaml")["conditions"]


def rules_version() -> str:
    """Combined version stored in every report, e.g. 'clinical 1.0.0 / monitoring 1.0.0 / ...'."""
    return " / ".join(
        f"{name} {data['version']}"
        for name, data in (
            ("clinical", clinical_rules()),
            ("monitoring", monitoring_rules()),
            ("comorbidity", _load("clinical/comorbidity-constraints.yaml")),
        )
    )
