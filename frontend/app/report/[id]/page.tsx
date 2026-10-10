import type { Metadata } from "next";
import { notFound } from "next/navigation";
import { Suspense } from "react";
import { ReportView } from "@/components/report/report-view";
import { fetchReport } from "@/lib/api";
import { ReportActions } from "./report-actions";

export const metadata: Metadata = {
  title: "Your report — Health Advisor",
  robots: { index: false, follow: false },
};

// Cache Components: the id is runtime data, so the fetch lives inside <Suspense> (never cached).
export default function Page({ params }: PageProps<"/report/[id]">) {
  return (
    <Suspense fallback={<p className="text-slate-600">Loading your report…</p>}>
      {params.then(({ id }) => (
        <ReportContent id={id} />
      ))}
    </Suspense>
  );
}

async function ReportContent({ id }: { id: string }) {
  const report = await fetchReport(id);
  if (!report) notFound();
  return (
    <div className="space-y-6">
      <ReportActions />
      <ReportView report={report} />
    </div>
  );
}
