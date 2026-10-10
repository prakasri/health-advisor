"use client";

// FS-F2 step 2: comorbidities ('none' is exclusive) and family history.
import { useRouter } from "next/navigation";
import { useState } from "react";
import { BooleanRadio, Button, Card, CheckboxGroup, StepHeader } from "@/components/ui";
import type { AssessmentInput } from "@/lib/api";
import { useDraft, useHydrated } from "@/lib/form-store";
import { COMORBIDITIES } from "@/lib/options";
import { useStepGuard } from "@/lib/use-guard";

type Condition = AssessmentInput["comorbidities"][number];

export default function StepTwo() {
  useStepGuard((d) => Boolean(d.step1Result?.eligible), "/assess/step-1");
  const router = useRouter();
  const hydrated = useHydrated();
  const { draft, update } = useDraft();
  const [errors, setErrors] = useState<{ comorbidities?: string; family?: string }>({});
  const selected = draft.comorbidities ?? [];

  function toggle(value: Condition) {
    let next: Condition[];
    if (value === "none") next = selected.includes("none") ? [] : ["none"];
    else {
      const withoutNone = selected.filter((c) => c !== "none");
      next = withoutNone.includes(value) ? withoutNone.filter((c) => c !== value) : [...withoutNone, value];
    }
    update({ comorbidities: next });
  }

  function submit(e: React.FormEvent) {
    e.preventDefault();
    const next: typeof errors = {};
    if (!selected.length) next.comorbidities = "Choose at least one option, or “None of these”.";
    if (draft.family_history === undefined) next.family = "Please answer yes or no.";
    setErrors(next);
    if (!Object.keys(next).length) router.push("/assess/step-3");
  }

  if (!hydrated) return null;

  return (
    <div className="space-y-6">
      <StepHeader
        step={2}
        title="Your health"
        intro="Other conditions change which foods, activities and check-ups matter most for you."
      />
      <Card>
        <form onSubmit={submit} noValidate className="space-y-6">
          <CheckboxGroup
            name="comorbidities"
            legend="Has a doctor told you that you have any of these? Select all that apply."
            options={COMORBIDITIES}
            values={selected}
            onToggle={toggle}
            error={errors.comorbidities}
            columns={2}
          />
          <BooleanRadio
            name="family_history"
            legend="Does a parent, brother or sister have diabetes?"
            value={draft.family_history}
            onChange={(family_history) => update({ family_history })}
            error={errors.family}
          />
          <div className="flex flex-wrap gap-3">
            <Button type="button" variant="secondary" onClick={() => router.push("/assess/step-1")}>
              Back
            </Button>
            <Button type="submit">Continue to step 3</Button>
          </div>
        </form>
      </Card>
    </div>
  );
}
