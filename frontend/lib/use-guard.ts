"use client";

import { useRouter } from "next/navigation";
import { useEffect } from "react";
import { type Draft, readDraft } from "./form-store";

/** Send the user back to `to` if they arrive at a step without completing the earlier ones. */
export function useStepGuard(ok: (d: Draft) => boolean, to: string) {
  const router = useRouter();
  useEffect(() => {
    if (!ok(readDraft())) router.replace(to);
    // run once on mount: the guard checks how the user arrived, not later edits
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);
}
