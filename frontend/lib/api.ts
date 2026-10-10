// API access (ARC-001). Types are generated from specs/architecture/openapi.yaml — run
// `npm run gen:types` after changing the contract.
import type { components } from "./api-types";

type Schemas = components["schemas"];

export type AssessmentInput = Schemas["assessment-input.schema"];
export type ClassifyRequest = Schemas["ClassifyRequest"];
export type ClassifyResponse = Schemas["ClassifyResponse"];
export type AssessmentResponse = Schemas["AssessmentResponse"];
export type Report = Schemas["report.schema"];
export type MealOption = Schemas["MealOption"];
export type MonitoringItem = Schemas["MonitoringItem"];

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
  ) {
    super(message);
  }
}

async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(path, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const message =
      res.status === 429
        ? "Too many assessments from this connection. Please wait a minute and try again."
        : res.status === 422
          ? "Some answers could not be accepted. Please check the form and try again."
          : "Something went wrong on our side. Please try again.";
    throw new ApiError(res.status, message);
  }
  return res.json() as Promise<T>;
}

// Browser calls go to /api/* on this domain; next.config.ts rewrites them to the backend.
export const classify = (body: ClassifyRequest) => post<ClassifyResponse>("/api/classify", body);

export const createAssessment = (body: AssessmentInput) =>
  post<AssessmentResponse>("/api/assessments", body);

// Server-side fetch (report and share pages): talk to the backend directly, never cached.
const apiOrigin = process.env.API_ORIGIN ?? "http://localhost:8000";

export async function fetchReport(reportId: string): Promise<Report | null> {
  const res = await fetch(`${apiOrigin}/api/reports/${encodeURIComponent(reportId)}`, {
    cache: "no-store",
  });
  if (res.status === 404 || res.status === 422) return null;
  if (!res.ok) throw new ApiError(res.status, "Could not load the report.");
  const body = (await res.json()) as Schemas["ReportEnvelope"];
  return body.report;
}
