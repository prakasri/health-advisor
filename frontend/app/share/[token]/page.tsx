import type { Metadata } from "next";
import { Suspense } from "react";
import { ReportView } from "@/components/report/report-view";
import { Card, LinkButton } from "@/components/ui";
import { fetchSharedReport } from "@/lib/api";

// UJ-5: read-only shared report. Never indexed; the token is runtime data, so it streams in Suspense.
export const metadata: Metadata = {
  title: "Shared health report — Health Advisor",
  robots: { index: false, follow: false },
};

export default function Page({ params }: PageProps<"/share/[token]">) {
  return (
    <Suspense fallback={<p className="text-slate-600">Loading the shared report…</p>}>
      {params.then(({ token }) => (
        <SharedReport token={token} />
      ))}
    </Suspense>
  );
}

async function SharedReport({ token }: { token: string }) {
  const report = await fetchSharedReport(token);
  if (!report) {
    return (
      <Card>
        <h1 className="text-2xl font-bold text-slate-900">This link is no longer available</h1>
        <p className="mt-2 text-slate-700">
          Shared reports expire after 30 days, and the person who shared it may have stopped sharing.
        </p>
        <LinkButton href="/" className="mt-5">
          Start your own assessment
        </LinkButton>
      </Card>
    );
  }
  return (
    <div className="space-y-6">
      <div className="no-print rounded-xl border border-sky-200 bg-sky-50 p-4 text-sky-950">
        Someone shared this educational health report with you. It is read-only.
      </div>
      <div className="no-print flex flex-wrap gap-3">
        <a
          href={`/api/share/${encodeURIComponent(token)}/pdf`}
          download
          className="inline-flex items-center justify-center rounded-lg bg-teal-700 px-5 py-3 text-base font-semibold text-white hover:bg-teal-800 focus-visible:outline focus-visible:outline-3 focus-visible:outline-offset-2 focus-visible:outline-teal-700"
        >
          Download PDF
        </a>
        <LinkButton href="/" variant="secondary">
          Start your own assessment
        </LinkButton>
      </div>
      <ReportView report={report} />
    </div>
  );
}
