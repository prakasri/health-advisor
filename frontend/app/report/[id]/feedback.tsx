"use client";

// FS-F5 F5.4: "Was this report helpful?" — one submission per page load.
import { useState } from "react";
import { Alert, Button } from "@/components/ui";
import { sendFeedback } from "@/lib/api";

export function Feedback({ reportId }: { reportId: string }) {
  const [helpful, setHelpful] = useState<boolean>();
  const [comment, setComment] = useState("");
  const [state, setState] = useState<"idle" | "sending" | "sent">("idle");
  const [error, setError] = useState<string>();

  async function submit(e: React.FormEvent) {
    e.preventDefault();
    if (helpful === undefined) return;
    setState("sending");
    setError(undefined);
    try {
      await sendFeedback(reportId, helpful, comment);
      setState("sent");
    } catch (err) {
      setState("idle");
      setError(err instanceof Error ? err.message : "Could not send feedback.");
    }
  }

  if (state === "sent") {
    return (
      <p role="status" className="no-print rounded-xl border border-slate-200 bg-white p-4 text-slate-800">
        Thank you — your feedback helps us improve these reports.
      </p>
    );
  }

  return (
    <form onSubmit={submit} className="no-print space-y-3 rounded-xl border border-slate-200 bg-white p-4">
      <fieldset>
        <legend className="font-medium text-slate-900">Was this report helpful?</legend>
        <div className="mt-2 flex gap-2">
          {[
            { v: true, label: "Yes" },
            { v: false, label: "No" },
          ].map((o) => (
            <label
              key={o.label}
              className={`cursor-pointer rounded-lg border px-4 py-2 has-[:focus-visible]:outline has-[:focus-visible]:outline-2 has-[:focus-visible]:outline-teal-700 ${
                helpful === o.v ? "border-teal-700 bg-teal-50" : "border-slate-300"
              }`}
            >
              <input
                type="radio"
                name="helpful"
                className="sr-only"
                checked={helpful === o.v}
                onChange={() => setHelpful(o.v)}
              />
              {o.label}
            </label>
          ))}
        </div>
      </fieldset>
      {helpful !== undefined && (
        <>
          <div>
            <label htmlFor="fb-comment" className="block text-sm font-medium text-slate-900">
              Anything we could do better? (optional)
            </label>
            <textarea
              id="fb-comment"
              maxLength={500}
              rows={3}
              value={comment}
              onChange={(e) => setComment(e.target.value)}
              aria-describedby="fb-hint"
              className="mt-1 w-full rounded-lg border border-slate-400 px-3 py-2 text-slate-900"
            />
            <p id="fb-hint" className="text-xs text-slate-500">
              Please don&apos;t include your name or contact details. {500 - comment.length} characters left.
            </p>
          </div>
          <Button type="submit" disabled={state === "sending"}>
            {state === "sending" ? "Sending…" : "Send feedback"}
          </Button>
        </>
      )}
      {error && <Alert tone="error">{error}</Alert>}
    </form>
  );
}
