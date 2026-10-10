"use client";

import { useRouter } from "next/navigation";
import { useState } from "react";
import { Button } from "@/components/ui";
import { useDraft } from "@/lib/form-store";

export function StartForm() {
  const router = useRouter();
  const { draft, update, clear } = useDraft();
  const [checked, setChecked] = useState(false);
  const [error, setError] = useState(false);

  function start(e: React.FormEvent) {
    e.preventDefault();
    if (!checked) {
      setError(true);
      return;
    }
    clear();
    update({ acknowledged: true });
    router.push("/assess/step-1");
  }

  return (
    <form onSubmit={start} noValidate className="space-y-4">
      <label className="flex items-start gap-3 text-slate-900">
        <input
          type="checkbox"
          checked={checked}
          onChange={(e) => {
            setChecked(e.target.checked);
            setError(false);
          }}
          aria-describedby={error ? "ack-error" : undefined}
          className="mt-1 h-5 w-5 accent-teal-700"
        />
        <span>I understand this is educational guidance, not a diagnosis or medical advice.</span>
      </label>
      {error && (
        <p id="ack-error" role="alert" className="text-sm font-medium text-red-700">
          Please confirm you understand before starting.
        </p>
      )}
      <div className="flex flex-wrap gap-3">
        <Button type="submit">Start the assessment</Button>
        {draft.step1Result && (
          <Button type="button" variant="secondary" onClick={() => router.push("/assess/step-1")}>
            Continue where I left off
          </Button>
        )}
      </div>
    </form>
  );
}
