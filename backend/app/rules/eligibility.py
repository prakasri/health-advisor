"""F1.3 eligibility screen (CLS-001 §1, GR-001 G1)."""

from typing import Literal

from app.rules.loader import clinical_rules

ExitReason = Literal["under_18", "pregnant", "type1"]


def exit_reason(age: int, pregnant: bool, type1_diabetes: bool) -> ExitReason | None:
    """Return the first matching exit reason, or None if the user is eligible."""
    rules = clinical_rules()["eligibility"]
    if age < rules["min_age"]:
        return "under_18"
    if pregnant and rules["exclude_pregnant"]:
        return "pregnant"
    if type1_diabetes and rules["exclude_type1"]:
        return "type1"
    return None


def referral_message(reason: ExitReason) -> str:
    return clinical_rules()["eligibility"]["messages"][reason].strip()
