"use client";

// UJ-2: ineligible exit. No further questions and no AI call.
import { Card, LinkButton } from "@/components/ui";
import { useDraft, useHydrated } from "@/lib/form-store";
import { formatHbA1c } from "@/lib/format";
import { useStepGuard } from "@/lib/use-guard";

export default function Referral() {
  useStepGuard((d) => d.step1Result?.eligible === false, "/");
  const hydrated = useHydrated();
  const { draft } = useDraft();
  const result = draft.step1Result;
  if (!hydrated || !result) return null;

  return (
    <Card>
      <h1 className="text-2xl font-bold text-slate-900">Please talk to your doctor about this result</h1>
      <p className="mt-3 text-slate-700">{result.referral_message}</p>
      <p className="mt-4 rounded-lg bg-slate-100 px-4 py-3 text-slate-800">
        HbA1c you entered: <strong>{formatHbA1c(result.hba1c!)}</strong>
      </p>
      <p className="mt-4 text-sm text-slate-600">
        This report is for educational and wellness purposes only. It is not a medical diagnosis and does
        not replace advice from a qualified healthcare professional.
      </p>
      <LinkButton href="/" variant="secondary" className="mt-5">
        Start again
      </LinkButton>
    </Card>
  );
}
