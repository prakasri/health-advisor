"""F4.1-F4.2 lab tests and screenings (CLS-001 §7, monitoring-rules.yaml)."""

from dataclasses import dataclass

from app.rules.loader import monitoring_rules
from app.schemas import MonitoringItem


@dataclass(frozen=True)
class MonitoringContext:
    classification: str
    urgent: bool
    comorbidities: frozenset[str]
    smoking: str
    alcohol: str
    diet: str
    family_history: bool
    age: int
    bmi_category: str


def _condition_matches(condition: dict, ctx: MonitoringContext) -> bool:
    """All keys in one condition must match (AND)."""
    for key, expected in condition.items():
        match key:
            case "always":
                ok = expected is True
            case "classification" | "smoking" | "alcohol" | "diet" | "bmi_category":
                ok = getattr(ctx, key) in expected
            case "comorbidity":
                ok = bool(ctx.comorbidities & set(expected))
            case "family_history" | "urgent":
                ok = getattr(ctx, key) is expected
            case "age_min":
                ok = ctx.age >= expected
            case _:
                raise ValueError(f"Unknown condition key {key!r} in monitoring-rules.yaml")
        if not ok:
            return False
    return True


def _any(conditions: list[dict], ctx: MonitoringContext) -> bool:
    return any(_condition_matches(c, ctx) for c in conditions)


def plan_monitoring(ctx: MonitoringContext) -> list[MonitoringItem]:
    selected = []
    for item in monitoring_rules()["items"]:
        if not _any(item["applies_when"], ctx):
            continue
        # Only the indicators that apply to this user are reported.
        matched = [
            h["indicator"] for h in item["highlight_when"] if _condition_matches(h["when"], ctx)
        ]
        selected.append(
            MonitoringItem(
                id=item["id"],
                name=item["name"],
                kind=item["kind"],
                why=item["why"],
                frequency=item["frequency"],
                risk_indicators=matched,
                highlighted=bool(matched),
            )
        )
    # Highlighted first, then labs, then screenings; file order within each group (stable sort).
    return sorted(selected, key=lambda m: (not m.highlighted, m.kind != "lab"))
