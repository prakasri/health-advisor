"""F1.2 HbA1c classification and F1.4 urgent flag (CLS-001 §2-3)."""

from dataclasses import dataclass
from decimal import ROUND_HALF_UP, Decimal
from typing import Literal

from app.rules.loader import clinical_rules

ClassificationId = Literal["normal", "prediabetes", "diabetes"]


@dataclass(frozen=True)
class Classification:
    hba1c: float  # rounded to one decimal
    classification: ClassificationId
    label: str
    explanation: str
    urgent: bool
    urgent_message: str | None


def round_half_up(value: float, places: str = "0.1") -> float:
    """Round like a person would (6.45 -> 6.5), not banker's rounding."""
    return float(Decimal(str(value)).quantize(Decimal(places), rounding=ROUND_HALF_UP))


def classify(hba1c: float) -> Classification:
    rules = clinical_rules()["hba1c"]
    if not rules["min"] <= hba1c <= rules["max"]:
        raise ValueError(f"HbA1c {hba1c} outside {rules['min']}-{rules['max']}")
    value = round_half_up(hba1c)
    band = next(b for b in rules["bands"] if b["min"] <= value < b["max_exclusive"])
    urgent = value >= rules["urgent_threshold"]
    return Classification(
        hba1c=value,
        classification=band["id"],
        label=band["label"],
        explanation=rules["explanations"][band["id"]].strip(),
        urgent=urgent,
        urgent_message=rules["urgent_message"].strip() if urgent else None,
    )
