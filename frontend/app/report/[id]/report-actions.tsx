"use client";

// FS-F5: PDF download (F5.2) and share link create / copy / revoke (F5.3).
import { useEffect, useState } from "react";
import { Alert, Button, LinkButton } from "@/components/ui";
import { createShareLink, revokeShareLink, type ShareLink } from "@/lib/api";

export function ReportActions({ reportId }: { reportId: string }) {
  const [link, setLink] = useState<ShareLink | null>(null);
  const [busy, setBusy] = useState(false);
  const [copied, setCopied] = useState(false);
  const [error, setError] = useState<string>();

  // Arriving from the form, start at the top of the report (urgent banner and summary first).
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);

  const url = link ? `${window.location.origin}${link.url_path}` : "";
  const expires = link
    ? new Date(link.expires_at).toLocaleDateString("en-GB", { day: "numeric", month: "long", year: "numeric" })
    : "";

  async function share() {
    setBusy(true);
    setError(undefined);
    try {
      setLink(await createShareLink(reportId));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not create a share link.");
    } finally {
      setBusy(false);
    }
  }

  async function copy() {
    try {
      await navigator.clipboard.writeText(url);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      setError("Copy failed — select the link and copy it manually.");
    }
  }

  async function stop() {
    if (!link) return;
    setBusy(true);
    try {
      await revokeShareLink(link.token);
      setLink(null);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not stop sharing.");
    } finally {
      setBusy(false);
    }
  }

  return (
    <div className="no-print space-y-3">
      <div className="flex flex-wrap gap-3">
        <a
          href={`/api/reports/${encodeURIComponent(reportId)}/pdf`}
          download
          className="inline-flex items-center justify-center rounded-lg bg-teal-700 px-5 py-3 text-base font-semibold text-white hover:bg-teal-800 focus-visible:outline focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-teal-700"
        >
          Download PDF
        </a>
        {!link && (
          <Button variant="secondary" onClick={share} disabled={busy}>
            {busy ? "Creating link…" : "Create share link"}
          </Button>
        )}
        <LinkButton href="/" variant="secondary">
          Start a new assessment
        </LinkButton>
      </div>

      {link && (
        <div className="rounded-xl border border-slate-200 bg-white p-4">
          <label htmlFor="share-url" className="block font-medium text-slate-900">
            Anyone with this link can view this report until {expires}.
          </label>
          <div className="mt-2 flex flex-wrap gap-2">
            <input
              id="share-url"
              readOnly
              value={url}
              onFocus={(e) => e.currentTarget.select()}
              className="min-w-0 flex-1 rounded-lg border border-slate-400 px-3 py-2 text-sm text-slate-900"
            />
            <Button variant="secondary" onClick={copy}>
              {copied ? "Copied" : "Copy link"}
            </Button>
            <Button variant="secondary" onClick={stop} disabled={busy}>
              Stop sharing
            </Button>
          </div>
          <p className="mt-2 text-sm text-slate-600">
            The link shows your report but not your name — we never collect it. Only share it with people you trust,
            such as your doctor or family.
          </p>
        </div>
      )}
      {error && <Alert tone="error">{error}</Alert>}
    </div>
  );
}
