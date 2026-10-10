"use client";

// UJ-001: answers live in sessionStorage between steps; nothing is sent until step 1 and step 3
// submit. Cleared once the report is created.
import { useCallback, useSyncExternalStore } from "react";
import type { AssessmentInput, ClassifyResponse } from "./api";

export type Draft = Partial<AssessmentInput> & {
  acknowledged?: boolean;
  step1Result?: ClassifyResponse;
};

const KEY = "health-advisor:draft";
const listeners = new Set<() => void>();
let cache: { raw: string | null; value: Draft } = { raw: null, value: {} };

function read(): Draft {
  let raw: string | null = null;
  try {
    raw = sessionStorage.getItem(KEY);
  } catch {
    return cache.value; // storage blocked (private mode): fall back to memory
  }
  if (raw !== cache.raw) {
    cache = { raw, value: raw ? (JSON.parse(raw) as Draft) : {} };
  }
  return cache.value;
}

function write(next: Draft) {
  const raw = JSON.stringify(next);
  cache = { raw, value: next };
  try {
    sessionStorage.setItem(KEY, raw);
  } catch {
    /* memory only */
  }
  listeners.forEach((l) => l());
}

const EMPTY: Draft = {};

export function useDraft() {
  const draft = useSyncExternalStore(
    (l) => {
      listeners.add(l);
      return () => listeners.delete(l);
    },
    read,
    () => EMPTY,
  );
  const update = useCallback((patch: Partial<Draft>) => write({ ...read(), ...patch }), []);
  const clear = useCallback(() => write({}), []);
  return { draft, update, clear };
}

/** Read the stored draft directly (safe inside effects, unlike the hydration snapshot). */
export const readDraft = read;

/** Hydration-safe flag: false on the server and during hydration, true afterwards. */
export function useHydrated() {
  return useSyncExternalStore(
    () => () => {},
    () => true,
    () => false,
  );
}
