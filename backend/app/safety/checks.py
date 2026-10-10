"""GR-001 §3 rule checks S1-S6 over the three LLM-written sections."""

import re
from collections.abc import Iterator
from dataclasses import dataclass, field
from functools import cache
from typing import Any

import yaml
from pydantic import BaseModel

from app.config import settings
from app.schemas import DietPlan, LifestylePlan, Narrative


@dataclass(frozen=True)
class Failure:
    check: str
    detail: str


@dataclass(frozen=True)
class CheckContext:
    diet: str  # vegetarian | non_vegetarian | vegan
    calorie_target: int
    hba1c: float
    bmi: float
    comorbidity_count: int
    constraint_checks: list[str] = field(default_factory=list)


@cache
def banned_terms() -> dict[str, Any]:
    with (settings.specs_dir / "ai/banned-terms.yaml").open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def _strings(value: Any) -> Iterator[str]:
    if isinstance(value, BaseModel):
        yield from _strings(value.model_dump())
    elif isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for v in value.values():
            yield from _strings(v)
    elif isinstance(value, list):
        for v in value:
            yield from _strings(v)


def _snippet(text: str) -> str:
    return text if len(text) <= 80 else text[:77] + "..."


def check_banned(sections: list[BaseModel]) -> list[Failure]:
    """S2: diagnostic, curative or medication language."""
    failures = []
    for text in (t for s in sections for t in _strings(s)):
        for rule in banned_terms()["banned"]:
            if re.search(rule["pattern"], text, re.IGNORECASE):
                failures.append(Failure("S2", f"banned '{rule['id']}' in: {_snippet(text)}"))
    return failures


def _forbidden_foods(diet: str) -> list[str]:
    terms = banned_terms()["diet_forbidden"]
    if diet == "vegetarian":
        return terms["vegetarian"]
    if diet == "vegan":
        return terms["vegetarian"] + terms["vegan_additional"]
    return []


# A forbidden word is fine when it is qualified as a plant alternative ("soy-based yogurt",
# "almond milk"), negated ("without paneer", "egg-free") or a comparison ("like scrambled eggs").
_PLANT_OR_NEGATION_BEFORE = re.compile(
    r"(?:\b(?:soy|soya|plant|almond|oat|coconut|cashew|peanut|rice|vegan|dairy[- ]free)"
    r"(?:[- ]based)?|\b(?:no|without|instead of|in place of|like|similar to|replaces?|"
    r"replacing|substitute for|alternative to)(?:\s+\w+)?)[\s-]*$",
    re.IGNORECASE,
)
_ALTERNATIVE_AFTER = re.compile(
    r"^(?:[- ]?free\b|[- ]style\b|\s+(?:alternative|substitute|replacement|style)s?\b"
    r"|\s*\([^)]*\b(?:free|vegan|plant-based|swap|alternative)\b)",
    re.IGNORECASE,
)


def _is_qualified(text: str, start: int, end: int) -> bool:
    return bool(
        _PLANT_OR_NEGATION_BEFORE.search(text[max(0, start - 30) : start])
        or _ALTERNATIVE_AFTER.match(text[end : end + 20])
    )


def check_diet_preference(plan: DietPlan, diet: str) -> list[Failure]:
    """S3: meal options and foods_to_eat respect the diet preference."""
    forbidden = _forbidden_foods(diet)
    if not forbidden:
        return []
    allow = sorted(banned_terms()["diet_allow_phrases"], key=len, reverse=True)
    meals = [*plan.breakfast, *plan.lunch, *plan.dinner, *plan.snacks]
    texts = [t for m in meals for t in (m.name, m.description, m.portion)] + plan.foods_to_eat
    failures = []
    for text in texts:
        cleaned = text.lower()
        for phrase in allow:
            cleaned = cleaned.replace(phrase, " " * len(phrase))
        for word in forbidden:
            for m in re.finditer(rf"\b{re.escape(word)}\b", cleaned):
                if not _is_qualified(cleaned, m.start(), m.end()):
                    failures.append(Failure("S3", f"'{word}' is not {diet}: {_snippet(text)}"))
                    break
    return failures


_KCAL = re.compile(r"(\d[\d,]*)\s*(?:kcal|calories)\b", re.IGNORECASE)
# "your HbA1c is 10% or higher" states a threshold, not the user's value: excluded.
_HBA1C = re.compile(
    r"\bhba1c\s+(?:is|of|was)\s+(\d+(?:\.\d+)?)\s*%(?!\s*or\s+(?:higher|above|more|lower|below))",
    re.IGNORECASE,
)
_BMI = re.compile(r"\bbmi\s+(?:is|of|was)\s+(\d+(?:\.\d+)?)", re.IGNORECASE)


def check_numbers(sections: list[BaseModel], ctx: CheckContext) -> list[Failure]:
    """S4: numbers in LLM text match the rule engine."""
    failures = []
    for text in (t for s in sections for t in _strings(s)):
        for m in _KCAL.finditer(text):
            if int(m.group(1).replace(",", "")) != ctx.calorie_target:
                failures.append(
                    Failure("S4", f"calorie number {m.group(1)} ≠ {ctx.calorie_target}")
                )
        for m in _HBA1C.finditer(text):
            if float(m.group(1)) != ctx.hba1c:
                failures.append(Failure("S4", f"HbA1c {m.group(1)}% ≠ {ctx.hba1c}%"))
        for m in _BMI.finditer(text):
            if float(m.group(1)) != ctx.bmi:
                failures.append(Failure("S4", f"BMI {m.group(1)} ≠ {ctx.bmi}"))
    return failures


_CONSTRAINT_PATTERNS = {
    "no_high_protein": re.compile(
        r"\bhigh[- ]protein\b|\bprotein\s+(?:shakes?|powders?|supplements?|bars?)\b", re.IGNORECASE
    ),
    # Encouragement or permission to drink, not a mere mention of alcohol.
    "no_alcohol_encouraged": re.compile(
        r"\b(?:enjoy|have|drink|allowed|fine|okay|ok|acceptable|safe)\b[^.]{0,40}"
        r"\b(?:alcohol|wine|beer|alcoholic drinks?)\b"
        r"|\b(?:alcohol|wine|beer|drinking)\b[^.]{0,40}"
        r"\b(?:in moderation|moderately|in small amounts|is fine|is okay|is ok)\b"
        r"|\b(?:a|one)\s+(?:glass|drink|peg)\s+of\b",
        re.IGNORECASE,
    ),
}
# A sentence that warns against something is compliant ("avoid protein powders").
_NEGATION = re.compile(
    r"\b(?:avoid\w*|limit\w*|not|don't|do not|never|no|cut out|steer clear|stop\w*|skip|"
    r"without|instead of|rather than|reduce\w*|beyond)\b",
    re.IGNORECASE,
)
_SENTENCE = re.compile(r"[^.;!?\n]+")


def _constraint_texts(sections: list[BaseModel]) -> Iterator[str]:
    """All LLM strings except lists of things to avoid, which are compliant by definition."""
    for section in sections:
        data = section.model_dump()
        data.pop("foods_to_avoid", None)
        yield from _strings(data)


def check_constraints(sections: list[BaseModel], ctx: CheckContext) -> list[Failure]:
    """S5: machine checks attached to comorbidity constraints (negation-aware)."""
    failures = []
    for check_id in ctx.constraint_checks:
        pattern = _CONSTRAINT_PATTERNS[check_id]
        for text in _constraint_texts(sections):
            for sentence in _SENTENCE.findall(text):
                if pattern.search(sentence) and not _NEGATION.search(sentence):
                    failures.append(Failure("S5", f"{check_id} violated: {_snippet(sentence)}"))
    return failures


def check_narrative_coverage(narrative: Narrative, ctx: CheckContext) -> list[Failure]:
    """S6: one comorbidity note per selected comorbidity."""
    if len(narrative.comorbidity_assessment) < ctx.comorbidity_count:
        return [
            Failure(
                "S6",
                f"comorbidity_assessment has {len(narrative.comorbidity_assessment)} entries, "
                f"expected {ctx.comorbidity_count}",
            )
        ]
    return []


def run_rule_checks(
    diet: DietPlan | None,
    lifestyle: LifestylePlan | None,
    narrative: Narrative | None,
    ctx: CheckContext,
) -> list[Failure]:
    """S1-S6. S1 = a section is missing (the LLM call failed or returned invalid output)."""
    missing = [
        Failure("S1", f"{name} missing or invalid")
        for name, value in (
            ("diet_plan", diet),
            ("lifestyle_plan", lifestyle),
            ("narrative", narrative),
        )
        if value is None
    ]
    if missing:
        return missing
    sections: list[BaseModel] = [diet, lifestyle, narrative]
    return [
        *check_banned(sections),
        *check_diet_preference(diet, ctx.diet),
        *check_numbers(sections, ctx),
        *check_constraints(sections, ctx),
        *check_narrative_coverage(narrative, ctx),
    ]
