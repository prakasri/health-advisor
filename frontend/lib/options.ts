// Form options and labels (FS-F2). Values match assessment-input.schema.json exactly.
import type { AssessmentInput } from "./api";

type Option<V extends string> = { value: V; label: string; hint?: string };

export const GENDERS: Option<AssessmentInput["gender"]>[] = [
  { value: "female", label: "Female" },
  { value: "male", label: "Male" },
  { value: "other", label: "Other / prefer not to say" },
];

export const COMORBIDITIES: Option<AssessmentInput["comorbidities"][number]>[] = [
  { value: "hypertension", label: "High blood pressure (hypertension)" },
  { value: "dyslipidemia", label: "High cholesterol or triglycerides (dyslipidemia)" },
  { value: "obesity", label: "Obesity" },
  { value: "cardiovascular_disease", label: "Heart or blood-vessel disease" },
  { value: "kidney_disease", label: "Kidney disease" },
  { value: "thyroid_disorder", label: "Thyroid disorder" },
  { value: "fatty_liver", label: "Fatty liver disease" },
  { value: "sleep_apnoea", label: "Sleep apnoea" },
  { value: "none", label: "None of these" },
];

export const ACTIVITY: Option<AssessmentInput["activity"]>[] = [
  { value: "sedentary", label: "Sedentary", hint: "Mostly sitting during the day" },
  { value: "lightly_active", label: "Lightly active", hint: "Light walking 1–3 days a week" },
  { value: "moderately_active", label: "Moderately active", hint: "Exercise 3–5 days a week" },
  { value: "very_active", label: "Very active", hint: "Hard exercise 6–7 days a week" },
];

export const SMOKING: Option<AssessmentInput["smoking"]>[] = [
  { value: "never", label: "Never smoked" },
  { value: "former", label: "Former smoker" },
  { value: "current", label: "Current smoker" },
];

export const ALCOHOL: Option<AssessmentInput["alcohol"]>[] = [
  { value: "none", label: "None" },
  { value: "occasional", label: "Occasional", hint: "A few drinks a month" },
  { value: "regular", label: "Regular", hint: "Most weeks" },
];

export const DIETS: Option<AssessmentInput["diet"]>[] = [
  { value: "vegetarian", label: "Vegetarian" },
  { value: "non_vegetarian", label: "Non-vegetarian" },
  { value: "vegan", label: "Vegan" },
];

export const REGIONS: Option<AssessmentInput["region"]>[] = [
  { value: "indian", label: "Indian" },
  { value: "mediterranean", label: "Mediterranean" },
  { value: "east_asian", label: "East Asian" },
  { value: "western", label: "Western" },
];

/** Display-only BMI estimate; the server recomputes it with the same CLS-001 rules. */
export function bmiEstimate(heightCm?: number, weightKg?: number, region?: string) {
  if (!heightCm || !weightKg || heightCm < 100 || weightKg < 25) return null;
  const bmi = Math.round((weightKg / (heightCm / 100) ** 2) * 10) / 10;
  const asian = region === "indian" || region === "east_asian";
  const [over, obese] = asian ? [23, 25] : [25, 30];
  const category =
    bmi < 18.5 ? "underweight" : bmi < over ? "healthy range" : bmi < obese ? "overweight" : "obese range";
  return { bmi, category, asian };
}
