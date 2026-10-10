"use client";

// Report actions. PDF download, share link and feedback arrive in Phase 7 (FS-F5 §F5.2-F5.4);
// until then the browser's print dialog can save the report as a PDF.
import { useEffect } from "react";
import { Button, LinkButton } from "@/components/ui";

export function ReportActions() {
  // Arriving from the form, start at the top of the report (urgent banner and summary first).
  useEffect(() => {
    window.scrollTo(0, 0);
  }, []);
  return (
    <div className="no-print flex flex-wrap gap-3">
      <Button variant="secondary" onClick={() => window.print()}>
        Print or save as PDF
      </Button>
      <LinkButton href="/" variant="secondary">
        Start a new assessment
      </LinkButton>
    </div>
  );
}
