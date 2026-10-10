"""F2.4 BMI and F3.1 calorie target (CLS-001 §4-5)."""

from typing import Literal

from app.rules.classify import round_half_up
from app.rules.loader import clinical_rules

BmiCategory = Literal["underweight", "normal", "overweight", "obese"]


def bmi(height_cm: float, weight_kg: float) -> float:
    return round_half_up(weight_kg / (height_cm / 100) ** 2)


def uses_asian_cutoffs(region: str) -> bool:
    return region in clinical_rules()["bmi"]["asian_regions"]


def bmi_category(bmi_value: float, region: str) -> BmiCategory:
    rules = clinical_rules()["bmi"]["cutoffs"]
    cut = rules["asian"] if uses_asian_cutoffs(region) else rules["standard"]
    if bmi_value < cut["underweight_below"]:
        return "underweight"
    if bmi_value < cut["overweight_from"]:
        return "normal"
    if bmi_value < cut["obese_from"]:
        return "overweight"
    return "obese"


def calorie_target(
    gender: str,
    age: int,
    height_cm: float,
    weight_kg: float,
    activity: str,
    category: BmiCategory,
) -> int:
    rules = clinical_rules()["calories"]
    c = rules["bmr"][gender]
    bmr = c["weight"] * weight_kg + c["height"] * height_cm + c["age"] * age + c["constant"]
    kcal = bmr * rules["activity_factor"][activity]
    if category in rules["deficit_if_bmi_category"]:
        kcal -= rules["deficit_kcal"]
    kcal = max(kcal, rules["floor_kcal"][gender])
    step = rules["round_to"]
    return int(round_half_up(kcal / step, "1")) * step
