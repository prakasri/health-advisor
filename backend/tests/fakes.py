"""FakeLLM (TS-001 §Fakes): scripted structured outputs per node, with call recording."""

import json
from collections.abc import Callable
from dataclasses import dataclass, field

from app.llm import LLMError
from app.rules import evaluate
from app.rules.risk import comorbidities, comorbidity_label
from app.safety.judge import JudgeVerdict
from app.schemas import AssessmentInput, DietPlan, LifestylePlan, MealOption, Narrative

Responder = Callable[
    [dict, int], object
]  # (payload, call_number starting at 1) -> output | Exception


@dataclass
class Call:
    node: str
    payload: dict


@dataclass
class FakeLLM:
    responders: dict[str, Responder]
    model_id: str = "fake-model"
    calls: list[Call] = field(default_factory=list)

    def generate(self, *, node, system, payload, output, effort):
        assert system, f"{node}: empty system prompt"
        json.dumps(payload)  # payload must be JSON-serialisable, as for the real client
        self.calls.append(Call(node, payload))
        result = self.responders[node](payload, self.count(node))
        if isinstance(result, Exception):
            raise result
        assert isinstance(result, output), f"{node}: fake returned {type(result).__name__}"
        return result

    def count(self, node: str) -> int:
        return sum(1 for c in self.calls if c.node == node)

    def nodes(self) -> list[str]:
        return [c.node for c in self.calls]


def _meal(name: str) -> MealOption:
    return MealOption(name=name, description=f"{name}, home style.", portion="1 bowl")


def good_diet(inp: AssessmentInput, extra_meal: str | None = None) -> DietPlan:
    kcal = evaluate(inp).calorie_target
    lunch = [_meal("Moong dal with brown rice"), _meal("Rajma with millet roti")]
    if extra_meal:
        lunch.append(_meal(extra_meal))
    return DietPlan(
        breakfast=[_meal("Vegetable poha"), _meal("Oats upma")],
        lunch=lunch,
        dinner=[_meal("Mixed vegetable sabzi with roti"), _meal("Chana salad bowl")],
        snacks=[_meal("Roasted chana"), _meal("Cucumber sticks")],
        foods_to_eat=["leafy greens", "lentils", "millets", "whole fruit", "nuts"],
        foods_to_avoid=["sugary drinks", "sweets", "maida", "fried snacks", "white bread"],
        portion_guidance="Half plate vegetables, quarter protein, quarter whole grains.",
        hydration="Drink water through the day.",
        based_on=[f"calorie target {kcal:,} kcal", inp.diet],
    )


def good_lifestyle(_: AssessmentInput) -> LifestylePlan:
    return LifestylePlan(
        exercise=["Brisk walking", "Bodyweight squats twice a week"],
        walking_goal="Start with 15 minutes on 5 days, build to 30 minutes.",
        weight_management="Aim for slow, steady progress.",
        sleep="Aim for 7-9 hours.",
        stress=["Slow breathing", "Short walks outdoors"],
        behaviour_change=["Plan meals weekly", "Track one habit"],
        based_on=["activity level"],
    )


def good_narrative(inp: AssessmentInput) -> Narrative:
    return Narrative(
        summary="Your HbA1c result is a useful starting point for small, steady changes.",
        comorbidity_assessment=[
            {"condition": comorbidity_label(c), "note": "This affects blood glucose."}
            for c in comorbidities(inp)
        ],
        preventive_actions=["Walk daily", "Choose whole grains", "Keep check-ups"],
        doctor_questions=["What target suits me?", "When should I retest?", "Which tests first?"],
    )


def scripted(inp: AssessmentInput, **overrides: Responder) -> FakeLLM:
    """A FakeLLM that returns safe outputs for `inp`, with per-node overrides."""
    responders: dict[str, Responder] = {
        "write_diet_plan": lambda p, n: good_diet(inp),
        "write_lifestyle_plan": lambda p, n: good_lifestyle(inp),
        "write_narrative": lambda p, n: good_narrative(inp),
        "safety_check": lambda p, n: JudgeVerdict(passed=True, problems=[]),
    }
    responders.update(overrides)
    return FakeLLM(responders)


def fail(message: str = "boom") -> Responder:
    return lambda p, n: LLMError(message)
