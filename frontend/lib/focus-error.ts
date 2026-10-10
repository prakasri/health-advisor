/** NFR-4: after a failed submit, move focus to the first field with an error so keyboard and
 * screen-reader users land on it. `keys` are element ids or radio/checkbox group names, in form order. */
export function focusFirstError(keys: string[], errors: Record<string, string | undefined>) {
  const first = keys.find((k) => errors[k]);
  if (!first) return;
  requestAnimationFrame(() => {
    const el = document.getElementById(first) ?? document.querySelector<HTMLElement>(`[name="${first}"]`);
    el?.focus();
  });
}
