import { LinkButton } from "@/components/ui";

export default function NotFound() {
  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold text-slate-900">This page is not available</h1>
      <p className="text-slate-700">
        The report may have expired or the link may be incorrect. Reports are kept for 90 days.
      </p>
      <LinkButton href="/">Start a new assessment</LinkButton>
    </div>
  );
}
