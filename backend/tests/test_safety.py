"""GR-001 rule checks S1-S6 (AC-4, AC-5, AC-6, AC-7) and the fallback content's own safety."""

import json

import pytest

from app.config import settings
from app.rules import evaluate
from app.rules.risk import comorbidities
from app.safety.checks import (
    CheckContext,
    check_banned,
    check_constraints,
    check_diet_preference,
    check_numbers,
    run_rule_checks,
)
from app.safety.fallback import fallback_diet, fallback_lifestyle, fallback_narrative
from app.schemas import AssessmentInput
from tests.fakes import good_diet, good_lifestyle, good_narrative

CASES = {
    c["id"]: c
    for c in map(
        json.loads, (settings.specs_dir / "quality/golden-cases.jsonl").read_text().splitlines()
    )
}
ELIGIBLE = [cid for cid, c in CASES.items() if c["expected"]["eligible"]]


def inp(case_id: str) -> AssessmentInput:
    return AssessmentInput.model_validate(CASES[case_id]["input"])


def ctx_for(case_id: str) -> CheckContext:
    i = inp(case_id)
    r = evaluate(i)
    return CheckContext(
        diet=i.diet,
        calorie_target=r.calorie_target,
        hba1c=r.classification.hba1c,
        bmi=r.bmi,
        comorbidity_count=len(comorbidities(i)),
        constraint_checks=r.risk.constraint_checks,
    )


# --- S3 diet preference (AC-4, recommendations.feature) --------------------------------------
@pytest.mark.parametrize(
    ("case_id", "food"), [("G02", "chicken curry"), ("G06", "paneer tikka"), ("G19", "egg bhurji")]
)
def test_forbidden_food_fails_s3(case_id, food):
    i = inp(case_id)
    failures = check_diet_preference(good_diet(i, extra_meal=food), i.diet)
    assert failures and {f.check for f in failures} == {"S3"}


@pytest.mark.parametrize("food", ["soy milk porridge", "peanut butter toast", "eggplant curry"])
def test_plant_alternatives_pass_s3(food):
    i = inp("G06")  # vegan
    assert check_diet_preference(good_diet(i, extra_meal=food), i.diet) == []


def test_non_vegetarian_has_no_food_restrictions():
    i = inp("G01")
    assert check_diet_preference(good_diet(i, extra_meal="chicken curry"), i.diet) == []


# --- S2 banned language (AC-7) ----------------------------------------------------------------
@pytest.mark.parametrize(
    "text",
    [
        "You have diabetes",
        "This plan can reverse your condition",
        "Stop taking your metformin",
        "Take 500 mg of cinnamon daily",
        "Bitter gourd cures diabetes",
    ],
)
def test_banned_language_fails_s2(text):
    n = good_narrative(inp("G02")).model_copy(update={"summary": text})
    assert {f.check for f in check_banned([n])} == {"S2"}


def test_range_wording_passes_s2():
    n = good_narrative(inp("G02")).model_copy(
        update={"summary": "Your HbA1c is in the diabetes range; a repeat test confirms it."}
    )
    assert check_banned([n]) == []


# --- S4 numbers (AC-6) ------------------------------------------------------------------------
def test_wrong_calorie_number_fails_s4():
    i = inp("G01")
    diet = good_diet(i).model_copy(update={"hydration": "Stay within 1,800 kcal."})
    assert [f.check for f in check_numbers([diet], ctx_for("G01"))] == ["S4"]


def test_correct_calorie_number_passes_s4():
    assert check_numbers([good_diet(inp("G01"))], ctx_for("G01")) == []  # mentions 1,500 kcal


def test_wrong_hba1c_and_bmi_fail_s4():
    n = good_narrative(inp("G02")).model_copy(
        update={"summary": "Your HbA1c is 8.1% and your BMI is 31.0."}
    )
    assert [f.check for f in check_numbers([n], ctx_for("G02"))] == ["S4", "S4"]


# --- S5 constraint checks (AC-5) --------------------------------------------------------------
@pytest.mark.parametrize(
    "text", ["Try a high-protein breakfast", "Add a protein shake after walks"]
)
def test_kidney_disease_rejects_high_protein(text):
    diet = good_diet(inp("G19")).model_copy(update={"portion_guidance": text})
    assert [f.check for f in check_constraints([diet], ctx_for("G19"))] == ["S5"]


def test_fatty_liver_rejects_moderate_alcohol():
    life = good_lifestyle(inp("G08")).model_copy(
        update={"sleep": "A glass of wine in moderation can help you relax."}
    )
    assert {f.check for f in check_constraints([life], ctx_for("G08"))} == {"S5"}


def test_constraint_check_not_applied_without_condition():
    diet = good_diet(inp("G02")).model_copy(update={"portion_guidance": "high-protein snack"})
    assert check_constraints([diet], ctx_for("G02")) == []


# --- S1 / S6 ----------------------------------------------------------------------------------
def test_missing_section_fails_s1_only():
    i = inp("G02")
    failures = run_rule_checks(good_diet(i), None, good_narrative(i), ctx_for("G02"))
    assert [f.check for f in failures] == ["S1"]


def test_narrative_must_cover_every_comorbidity_s6():
    i = inp("G20")  # 8 comorbidities
    narrative = good_narrative(i).model_copy(update={"comorbidity_assessment": []})
    failures = run_rule_checks(good_diet(i), good_lifestyle(i), narrative, ctx_for("G20"))
    assert [f.check for f in failures] == ["S6"]


# --- the fallback content must itself pass every rule check -----------------------------------
@pytest.mark.parametrize("case_id", ELIGIBLE)
def test_fallback_content_passes_all_checks(case_id):
    i, r = inp(case_id), evaluate(inp(case_id))
    failures = run_rule_checks(
        fallback_diet(i, r), fallback_lifestyle(i, r), fallback_narrative(i, r), ctx_for(case_id)
    )
    assert failures == []


def test_threshold_wording_is_not_a_wrong_hba1c():
    n = good_narrative(inp("G05")).model_copy(update={"summary": "Your HbA1c is 10% or higher."})
    assert check_numbers([n], ctx_for("G05")) == []


# --- regressions from the first live run (EV-001 Tier 3, 2026-10-10) -------------------------
@pytest.mark.parametrize(
    ("case_id", "food"),
    [
        ("G09", "Sliced apple or pear with a small cup of plain soy-based yogurt alternative"),
        ("G11", "Crumbled tofu with onions and spinach, like scrambled eggs"),
        ("G11", "Egg-free tofu bhurji"),
        ("G06", "Cashew cheese on whole-grain toast"),
        ("G06", "Dosa without ghee"),
        ("G06", "Layered eggplant and soy mince with a light soy-milk bechamel"),
        ("G06", "Oat-milk porridge with berries"),
        ("G11", "Vegetable Omelette (egg-free swap) - Chickpea Flour Scramble"),
    ],
)
def test_plant_alternatives_and_comparisons_pass_s3(case_id, food):
    i = inp(case_id)
    assert check_diet_preference(good_diet(i, extra_meal=food), i.diet) == []


@pytest.mark.parametrize(
    ("case_id", "food"),
    [("G11", "Tofu and egg curry"), ("G06", "No-oil paneer tikka"), ("G09", "Oats with honey")],
)
def test_real_violations_still_fail_s3(case_id, food):
    i = inp(case_id)
    assert {f.check for f in check_diet_preference(good_diet(i, extra_meal=food), i.diet)} == {"S3"}


@pytest.mark.parametrize(
    ("case_id", "field", "text"),
    [
        (
            "G19",
            "portion_guidance",
            "Maintain moderate protein intake, avoiding high-protein diets.",
        ),
        ("G19", "portion_guidance", "Do not use protein powders or protein bars."),
        ("G08", "based_on", ["Occasional alcohol use"]),
        ("G08", "hydration", "Occasional alcohol use: advised to avoid alcohol completely."),
    ],
)
def test_warnings_and_echoed_inputs_pass_s5(case_id, field, text):
    diet = good_diet(inp(case_id)).model_copy(update={field: text})
    assert check_constraints([diet], ctx_for(case_id)) == []


def test_foods_to_avoid_never_trigger_s5():
    diet = good_diet(inp("G19")).model_copy(
        update={"foods_to_avoid": ["Protein powders, protein bars or high-protein supplements"] * 5}
    )
    assert check_constraints([diet], ctx_for("G19")) == []


@pytest.mark.parametrize(
    "text",
    [
        "Enjoy a glass of wine with dinner.",
        "Alcohol is fine in moderation.",
        "Have a beer at weekends.",
    ],
)
def test_alcohol_encouragement_still_fails_for_fatty_liver(text):
    life = good_lifestyle(inp("G08")).model_copy(update={"sleep": text})
    assert {f.check for f in check_constraints([life], ctx_for("G08"))} == {"S5"}


def test_insulin_as_physiology_is_allowed_but_medication_advice_is_not():
    i = inp("G15")
    ok = good_narrative(i).model_copy(
        update={"summary": "Weight makes it harder to use your own insulin."}
    )
    bad = good_narrative(i).model_copy(
        update={"summary": "You can reduce your insulin as you lose weight."}
    )
    assert check_banned([ok]) == []
    assert {f.check for f in check_banned([bad])} == {"S2"}


def test_cured_foods_are_not_a_cure_claim():
    i = inp("G11")
    avoid = good_diet(i).model_copy(update={"hydration": "Limit excess salty or cured foods."})
    claim = good_narrative(i).model_copy(update={"summary": "Many people are cured of diabetes."})
    assert check_banned([avoid]) == []
    assert {f.check for f in check_banned([claim])} == {"S2"}
