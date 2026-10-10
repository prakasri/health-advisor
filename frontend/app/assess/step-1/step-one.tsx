"use client";

// FS-F1 / UJ-1 steps 2-3: HbA1c and eligibility, classified immediately by POST /api/classify.
import { useRouter } from "next/navigation";
import { useRef, useState } from "react";
import { Alert, BooleanRadio, Button, Card, NumberField, RadioGroup, StepHeader } from "@/components/ui";
import { classify } from "@/lib/api";
import { useDraft, useHydrated } from "@/lib/form-store";
import { formatHbA1c } from "@/lib/format";
import { GENDERS } from "@/lib/options";
import { useStepGuard } from "@/lib/use-guard";

type Errors = Partial<Record<"hba1c" | "age" | "gender" | "pregnant" | "type1" | "form", string>>;

function parseNumber(text: string) {
  const n = Number(text.trim().replace(",", "."));
  return text.trim() === "" || Number.isNaN(n) ? undefined : n;
}

export function StepOne() {
  useStepGuard((d) => Boolean(d.acknowledged), "/");
  const router = useRouter();
  const hydrated = useHydrated();
  const { draft, update } = useDraft();
  const [hba1cText, setHba1cText] = useState<string>();
  const [ageText, setAgeText] = useState<string>();
  const [errors, setErrors] = useState<Errors>({});
  const [busy, setBusy] = useState(false);
  const resultRef = useRef<HTMLDivElement>(null);

  const hba1cValue = hba1cText ?? (draft.hba1c?.toString() || "");
  const ageValue = ageText ?? (draft.age?.toString() || "");
  const askPregnancy = draft.gender === "female" || draft.gender === "other";
  const result = draft.step1Result;
  // Any edit invalidates a previous result, so nobody continues with a stale classification.
  const edit = (patch: Parameters<typeof update>[0]) => update({ ...patch, step1Result: undefined });

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    const hba1c = parseNumber(hba1cValue);
    const age = parseNumber(ageValue);
    const next: Errors = {};
    if (hba1c === undefined || hba1c < 3 || hba1c > 20)
      next.hba1c = "Enter your HbA1c as a percentage between 3.0 and 20.0, for example 6.2.";
    if (age === undefined || !Number.isInteger(age) || age < 1 || age > 120) next.age = "Enter your age in whole years.";
    if (!draft.gender) next.gender = "Please choose an option.";
    if (askPregnancy && draft.pregnant === undefined) next.pregnant = "Please answer yes or no.";
    if (draft.type1_diabetes === undefined) next.type1 = "Please answer yes or no.";
    setErrors(next);
    if (Object.keys(next).length) return;

    const pregnant = askPregnancy ? Boolean(draft.pregnant) : false;
    setBusy(true);
    try {
      const res = await classify({ hba1c: hba1c!, age: age!, pregnant, type1_diabetes: draft.type1_diabetes! });
      update({ hba1c: Math.round(hba1c! * 10) / 10, age: age!, pregnant, step1Result: res });
      requestAnimationFrame(() => resultRef.current?.focus());
    } catch (err) {
      setErrors({ form: err instanceof Error ? err.message : "Something went wrong. Please try again." });
    } finally {
      setBusy(false);
    }
  }

  if (!hydrated) return null;

  return (
    <div className="space-y-6">
      <StepHeader step={1} title="Your HbA1c" intro="Use the result from your most recent HbA1c blood test." />
      <Card>
        <form onSubmit={submit} noValidate className="space-y-6">
          <NumberField
            id="hba1c"
            label="HbA1c result"
            hint="Shown as a percentage on your lab report, for example 6.2%."
            unit="%"
            value={hba1cValue}
            onChange={(e) => {
              setHba1cText(e.target.value);
              if (result) edit({});
            }}
            error={errors.hba1c}
          />
          <NumberField
            id="age"
            label="Age"
            unit="years"
            inputMode="numeric"
            value={ageValue}
            onChange={(e) => {
              setAgeText(e.target.value);
              if (result) edit({});
            }}
            error={errors.age}
          />
          <RadioGroup
            name="gender"
            legend="Sex"
            options={GENDERS}
            value={draft.gender}
            onChange={(gender) => edit({ gender, ...(gender === "male" ? { pregnant: false } : {}) })}
            error={errors.gender}
          />
          {askPregnancy && (
            <BooleanRadio
              name="pregnant"
              legend="Are you pregnant?"
              value={draft.pregnant}
              onChange={(pregnant) => edit({ pregnant })}
              error={errors.pregnant}
            />
          )}
          <BooleanRadio
            name="type1"
            legend="Have you been told you have type 1 diabetes?"
            value={draft.type1_diabetes}
            onChange={(type1_diabetes) => edit({ type1_diabetes })}
            error={errors.type1}
          />
          {errors.form && <Alert tone="error">{errors.form}</Alert>}
          <Button type="submit" disabled={busy}>
            {busy ? "Checking…" : "See my result"}
          </Button>
        </form>
      </Card>

      {result && (
        <div ref={resultRef} tabIndex={-1} aria-live="polite" className="space-y-4 outline-none">
          {result.eligible ? (
            <Card>
              {result.urgent && result.urgent_message && (
                <div className="mb-4">
                  <Alert tone="warning" title="Please see a doctor soon">
                    {result.urgent_message}
                  </Alert>
                </div>
              )}
              <p className="text-sm font-medium text-slate-600">Your HbA1c of {formatHbA1c(result.hba1c!)}</p>
              <p className="mt-1 text-2xl font-bold text-slate-900">{result.label}</p>
              <p className="mt-2 text-slate-700">{result.explanation}</p>
              <Button className="mt-5" onClick={() => router.push("/assess/step-2")}>
                Continue to step 2
              </Button>
            </Card>
          ) : (
            <Card>
              <p className="text-xl font-bold text-slate-900">This tool isn&apos;t the right fit for you</p>
              <p className="mt-2 text-slate-700">{result.referral_message}</p>
              <Button className="mt-5" variant="secondary" onClick={() => router.push("/assess/referral")}>
                Continue
              </Button>
            </Card>
          )}
        </div>
      )}
    </div>
  );
}
