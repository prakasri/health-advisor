"""Unit tests for CLS-001 rules: boundaries, formulas, ordering and spec integrity."""

import pytest

from app.rules import (
    MonitoringContext,
    bmi,
    bmi_category,
    calorie_target,
    classify,
    exit_reason,
    plan_monitoring,
    referral_message,
)
from app.rules.loader import clinical_rules, monitoring_rules
from app.rules.monitoring import _condition_matches


# --- F1.2 classification (AC-1) -------------------------------------------------------------
@pytest.mark.parametrize(
    ("hba1c", "expected", "rounded"),
    [
        (3.0, "normal", 3.0),
        (5.6, "normal", 5.6),
        (5.64, "normal", 5.6),
        (5.65, "prediabetes", 5.7),
        (5.7, "prediabetes", 5.7),
        (6.4, "prediabetes", 6.4),
        (6.44, "prediabetes", 6.4),
        (6.45, "diabetes", 6.5),
        (6.5, "diabetes", 6.5),
        (20.0, "diabetes", 20.0),
    ],
)
def test_classification_boundaries(hba1c, expected, rounded):
    result = classify(hba1c)
    assert result.classification == expected
    assert result.hba1c == rounded


@pytest.mark.parametrize("hba1c", [2.9, 20.1, -1, 100])
def test_out_of_range_hba1c_raises(hba1c):
    with pytest.raises(ValueError):
        classify(hba1c)


def test_labels_use_range_wording():
    for value in (5.0, 6.0, 7.0):
        assert classify(value).label.startswith("In the ")
        assert "you have" not in classify(value).explanation.lower()


# --- F1.4 urgent flag (AC-3) ----------------------------------------------------------------
@pytest.mark.parametrize(
    ("hba1c", "urgent"), [(9.9, False), (9.94, False), (9.95, True), (10.0, True)]
)
def test_urgent_threshold(hba1c, urgent):
    result = classify(hba1c)
    assert result.urgent is urgent
    assert (result.urgent_message is not None) is urgent


# --- F1.3 eligibility (AC-2) ----------------------------------------------------------------
@pytest.mark.parametrize(
    ("age", "pregnant", "type1", "reason"),
    [
        (18, False, False, None),
        (17, False, False, "under_18"),
        (30, True, False, "pregnant"),
        (30, False, True, "type1"),
        (17, True, True, "under_18"),  # first rule wins
        (30, True, True, "pregnant"),
    ],
)
def test_eligibility_order(age, pregnant, type1, reason):
    assert exit_reason(age, pregnant, type1) == reason


@pytest.mark.parametrize("reason", ["under_18", "pregnant", "type1"])
def test_referral_messages_exist(reason):
    assert len(referral_message(reason)) > 50


# --- F2.4 BMI -------------------------------------------------------------------------------
def test_bmi_formula_and_rounding():
    assert bmi(172, 80) == 27.0
    assert bmi(155, 68) == 28.3


@pytest.mark.parametrize(
    ("value", "region", "category"),
    [
        (18.4, "western", "underweight"),
        (18.5, "western", "normal"),
        (24.9, "western", "normal"),
        (25.0, "western", "overweight"),
        (29.9, "western", "overweight"),
        (30.0, "western", "obese"),
        (22.9, "indian", "normal"),
        (23.0, "indian", "overweight"),
        (24.9, "east_asian", "overweight"),
        (25.0, "east_asian", "obese"),
        (25.0, "mediterranean", "overweight"),
    ],
)
def test_bmi_categories(value, region, category):
    assert bmi_category(value, region) == category


# --- F3.1 calorie target --------------------------------------------------------------------
def test_calorie_worked_example_meena_hits_floor():
    # CLS-001 §5 worked example
    assert calorie_target("female", 58, 155, 68, "sedentary", "obese") == 1200


def test_calorie_no_deficit_when_normal_weight():
    # 10*72 + 6.25*178 - 5*30 + 5 = 1687.5; * 1.725 = 2910.9 -> 2900
    assert calorie_target("male", 30, 178, 72, "very_active", "normal") == 2900


def test_calorie_other_gender_uses_mean_constant():
    # 700 + 1062.5 - 275 - 78 = 1409.5; * 1.55 = 2184.7; -500 = 1684.7 -> 1700
    assert calorie_target("other", 55, 170, 70, "moderately_active", "overweight") == 1700


@pytest.mark.parametrize("gender", ["female", "male", "other"])
def test_calorie_target_is_multiple_of_50_and_above_floor(gender):
    floor = clinical_rules()["calories"]["floor_kcal"][gender]
    kcal = calorie_target(gender, 80, 150, 45, "sedentary", "obese")
    assert kcal % 50 == 0
    assert kcal >= floor


# --- F4 monitoring --------------------------------------------------------------------------
def _ctx(**overrides) -> MonitoringContext:
    base = dict(
        classification="diabetes",
        urgent=False,
        comorbidities=frozenset(),
        smoking="never",
        alcohol="none",
        diet="non_vegetarian",
        family_history=False,
        age=40,
        bmi_category="normal",
    )
    return MonitoringContext(**{**base, **overrides})


def test_monitoring_order_highlighted_then_labs_then_screenings():
    items = plan_monitoring(_ctx(comorbidities=frozenset({"hypertension"})))
    highlighted = [i for i in items if i.highlighted]
    rest = [i for i in items if not i.highlighted]
    assert items[: len(highlighted)] == highlighted
    kinds = [i.kind for i in rest]
    assert kinds == sorted(kinds, key=lambda k: k != "lab")


def test_monitoring_has_no_duplicate_names():
    for cls in ("normal", "prediabetes", "diabetes"):
        names = [i.name for i in plan_monitoring(_ctx(classification=cls))]
        assert len(names) == len(set(names))


def test_condition_keys_are_anded():
    # liver check: obesity AND (prediabetes or diabetes)
    assert not _condition_matches(
        {"comorbidity": ["obesity"], "classification": ["diabetes"]},
        _ctx(classification="normal", comorbidities=frozenset({"obesity"})),
    )


def test_every_monitoring_condition_key_is_known():
    ctx = _ctx()
    for item in monitoring_rules()["items"]:
        for condition in item["applies_when"] + item["highlight_when"]:
            _condition_matches(condition, ctx)  # raises ValueError on an unknown key


def test_unknown_condition_key_raises():
    with pytest.raises(ValueError):
        _condition_matches({"shoe_size": [42]}, _ctx())


def test_unknown_risk_factor_key_raises():
    from app.rules.risk import _matches
    from app.schemas import AssessmentInput

    inp = AssessmentInput.model_validate(
        dict(
            hba1c=6.0,
            age=40,
            gender="male",
            pregnant=False,
            type1_diabetes=False,
            comorbidities=["none"],
            family_history=False,
            height_cm=170,
            weight_kg=70,
            activity="sedentary",
            smoking="never",
            alcohol="none",
            diet="vegan",
            region="western",
        )
    )
    with pytest.raises(ValueError):
        _matches({"shoe_size": 42}, inp, "normal", "normal")


def test_rules_version_names_all_rule_files():
    from app.rules.loader import rules_version

    version = rules_version()
    for name in ("clinical", "monitoring", "comorbidity"):
        assert name in version
