# GENERATED from specs/data/schemas/assessment-input.schema.json — do not edit. Run scripts/gen_schemas.sh.

from __future__ import annotations

from typing import Annotated, Literal
from pydantic import BaseModel, ConfigDict, Field


class AssessmentInput(BaseModel):
    model_config = ConfigDict(
        extra="forbid",
    )
    hba1c: Annotated[
        float, Field(description="HbA1c in percent (NGSP), one decimal place.", ge=3.0, le=20.0)
    ]
    age: Annotated[int, Field(ge=1, le=120)]
    gender: Literal["female", "male", "other"]
    pregnant: bool
    type1_diabetes: Annotated[
        bool, Field(description="User has been told they have type 1 diabetes.")
    ]
    comorbidities: Annotated[
        list[
            Literal[
                "none",
                "hypertension",
                "dyslipidemia",
                "obesity",
                "cardiovascular_disease",
                "kidney_disease",
                "thyroid_disorder",
                "fatty_liver",
                "sleep_apnoea",
            ]
        ],
        Field(description="'none' is mutually exclusive with every other value.", min_length=1),
    ]
    family_history: Annotated[bool, Field(description="Parent or sibling with diabetes.")]
    height_cm: Annotated[float, Field(ge=100.0, le=250.0)]
    weight_kg: Annotated[float, Field(ge=25.0, le=300.0)]
    activity: Literal["sedentary", "lightly_active", "moderately_active", "very_active"]
    smoking: Literal["never", "former", "current"]
    alcohol: Literal["none", "occasional", "regular"]
    diet: Literal["vegetarian", "non_vegetarian", "vegan"]
    region: Annotated[
        Literal["indian", "mediterranean", "east_asian", "western"],
        Field(
            description="Cuisine region for meal examples; also selects Asian BMI cut-offs for indian and east_asian."
        ),
    ]
