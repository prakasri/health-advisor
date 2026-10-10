import type { Metadata } from "next";
import { StepOne } from "./step-one";

export const metadata: Metadata = { title: "Step 1: Your HbA1c — Health Advisor" };

export default function Page() {
  return <StepOne />;
}
