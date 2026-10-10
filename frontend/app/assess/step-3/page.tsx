"use client";

// FS-F2 step 3: body measurements (live BMI), activity, smoking, alcohol, diet and region,
// then POST /api/assessments and go to the report (UJ-1 steps 5-7).
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";
import { Alert, Button, Card, NumberField, RadioGroup, StepHeader } from "@/components/ui";
import { type AssessmentInput, createAssessment } from "@/lib/api";
import { readDraft, useDraft, useHydrated } from "@/lib/form-store";
import { ACTIVITY, ALCOHOL, DIETS, REGIONS, SMOKING, bmiEstimate } from "@/lib/options";
import { useStepGuard } from "@/lib/use-guard";

const PROGRESS = [
  "Checking your results against clinical guidelines…",
  "Building a food plan that fits your diet…",
  "Writing your activity plan…",
  "Running a safety review of your report…",
];

type Field = "height" | "weight" | "activity" | "smoking" | "alcohol" | "diet" | "region" | "form";

function parse(text: string) {
  const n = Number(text.trim().replace(",", "."));
  return text.trim() === "" || Number.isNaN(n) ? undefined : n;
}

export default function StepThree() {
  useStepGuard((d) => Boolean(d.step1Result?.eligible && d.comorbidities?.length), "/assess/step-2");
  const router = useRouter();
  const hydrated = useHydrated();
  const { draft, update, clear } = useDraft();
  const [heightText, setHeightText] = useState<string>();
  const [weightText, setWeightText] = useState<string>();
  const [errors, setErrors] = useState<Partial<Record<Field, string>>>({});
  const [busy, setBusy] = useState(false);
  const [progress, setProgress] = useState(0);

  // Default the cuisine region from the browser locale; the user can change it.
  useEffect(() => {
    if (!readDraft().region && navigator.language.toLowerCase().endsWith("-in")) update({ region: "indian" });
  }, [update]);

  useEffect(() => {
    if (!busy) return;
    const timer = setInterval(() => setProgress((p) => Math.min(p + 1, PROGRESS.length - 1)), 5000);
    return () => clearInterval(timer);
  }, [busy]);

  const heightValue = heightText ?? (draft.height_cm?.toString() || "");
  const weightValue = weightText ?? (draft.weight_kg?.toString() || "");
  const bmi = bmiEstimate(parse(heightValue), parse(weightValue), draft.region);

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const height = parse(heightValue);
    const weight = parse(weightValue);
    const next: Partial<Record<Field, string>> = {};
    if (height === undefined || height < 100 || height > 250) next.height = "Enter your height in centimetres (100–250).";
    if (weight === undefined || weight < 25 || weight > 300) next.weight = "Enter your weight in kilograms (25–300).";
    for (const f of ["activity", "smoking", "alcohol", "diet", "region"] as const) {
      if (!draft[f]) next[f] = "Please choose an option.";
    }
    setErrors(next);
    if (Object.keys(next).length) return;

    update({ height_cm: height, weight_kg: weight });
    const d = readDraft();
    const body: AssessmentInput = {
      hba1c: d.hba1c!,
      age: d.age!,
      gender: d.gender!,
      pregnant: d.pregnant ?? false,
      type1_diabetes: d.type1_diabetes ?? false,
      comorbidities: d.comorbidities!,
      family_history: d.family_history!,
      height_cm: height!,
      weight_kg: weight!,
      activity: d.activity!,
      smoking: d.smoking!,
      alcohol: d.alcohol!,
      diet: d.diet!,
      region: d.region!,
    };
    setBusy(true);
    setProgress(0);
    try {
      const res = await createAssessment(body);
      clear();
      router.push(`/report/${res.report_id}`);
    } catch (err) {
      setBusy(false);
      setErrors({ form: err instanceof Error ? err.message : "Something went wrong. Please try again." });
    }
  }

  if (!hydrated) return null;

  if (busy) {
    return (
      <Card className="text-center">
        <div className="mx-auto h-10 w-10 animate-spin rounded-full border-4 border-teal-200 border-t-teal-700" aria-hidden="true" />
        <h1 className="mt-4 text-xl font-bold text-slate-900">Preparing your report</h1>
        <p role="status" aria-live="polite" className="mt-2 text-slate-700">
          {PROGRESS[progress]}
        </p>
        <p className="mt-4 text-sm text-slate-500">This usually takes about 20 seconds.</p>
      </Card>
    );
  }

  return (
    <div className="space-y-6">
      <StepHeader step={3} title="Your lifestyle" intro="This shapes your calorie target, meal ideas and activity plan." />
      <Card>
        <form onSubmit={submit} noValidate className="space-y-6">
          <div className="grid gap-6 sm:grid-cols-2">
            <NumberField
              id="height"
              label="Height"
              unit="cm"
              value={heightValue}
              onChange={(e) => setHeightText(e.target.value)}
              error={errors.height}
            />
            <NumberField
              id="weight"
              label="Weight"
              unit="kg"
              value={weightValue}
              onChange={(e) => setWeightText(e.target.value)}
              error={errors.weight}
            />
          </div>
          <p aria-live="polite" className="rounded-lg bg-slate-100 px-4 py-3 text-slate-800">
            {bmi ? (
              <>
                Estimated BMI <strong>{bmi.bmi}</strong> — {bmi.category}
                {bmi.asian && " (using cut-offs recommended for South and East Asian people)"}
              </>
            ) : (
              "Your BMI will appear here once you enter height and weight."
            )}
          </p>
          <RadioGroup name="activity" legend="How active are you?" options={ACTIVITY} value={draft.activity} onChange={(activity) => update({ activity })} error={errors.activity} columns={2} />
          <RadioGroup name="smoking" legend="Do you smoke?" options={SMOKING} value={draft.smoking} onChange={(smoking) => update({ smoking })} error={errors.smoking} columns={2} />
          <RadioGroup name="alcohol" legend="Do you drink alcohol?" options={ALCOHOL} value={draft.alcohol} onChange={(alcohol) => update({ alcohol })} error={errors.alcohol} columns={2} />
          <RadioGroup name="diet" legend="Diet preference" options={DIETS} value={draft.diet} onChange={(diet) => update({ diet })} error={errors.diet} columns={2} />
          <RadioGroup name="region" legend="Which cuisine do you mostly eat?" options={REGIONS} value={draft.region} onChange={(region) => update({ region })} error={errors.region} columns={2} />
          {errors.form && <Alert tone="error">{errors.form}</Alert>}
          <div className="flex flex-wrap gap-3">
            <Button type="button" variant="secondary" onClick={() => router.push("/assess/step-2")}>
              Back
            </Button>
            <Button type="submit">Create my report</Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
