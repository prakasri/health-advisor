---
id: Q-08
title: Accessibility checklist (WCAG 2.2 AA basics)
status: approved
version: 1.0.0
depends_on: [PRD-001, TS-001]
implements: [NFR-4, NFR-9]
last_reviewed: 2026-10-10
---

# Q-08 Accessibility checklist

Checked on 2026-10-10 in Chrome against the local build (frontend `8c96369`+, Phase 9 fixes).
Method: keyboard-only walkthrough, DOM inspection (focus order, labels, ARIA), computed contrast
from Tailwind v4's OKLCH palette, and a 360 px viewport frame.

| # | Check | WCAG | Result | Evidence |
| --- | --- | --- | --- | --- |
| 1 | Skip link is first in tab order and visible on focus | 2.4.1 | Pass | "Skip to content" appears top-left (136 × 40 px, white on page) when focused |
| 2 | Logical focus order | 2.4.3 | Pass | Landing: skip link → logo → acknowledgement → Start. Step 1: HbA1c → age → sex → (pregnancy) → type 1 → submit |
| 3 | Visible focus indicator on every control | 2.4.7 | Pass | Teal outline on buttons, links, inputs; option cards outline via `:has(:focus-visible)` |
| 4 | Whole journey operable by keyboard | 2.1.1 | Pass | Ticked box with Space, started with Enter, typed fields, chose radios with Space / arrow keys, submitted with Enter |
| 5 | Every input has a programmatic label | 1.3.1, 4.1.2 | Pass | `<label for>` on number fields; radio/checkbox inputs wrapped in `<label>`; groups use `<fieldset>`/`<legend>` |
| 6 | Errors identified and described | 3.3.1, 3.3.3 | Pass | Invalid fields get `aria-invalid="true"` and `aria-describedby` → hint + error text with a concrete fix ("…between 3.0 and 20.0, for example 6.2") |
| 7 | Focus moves to the first error after a failed submit | 3.3.1 | Pass (fixed in Phase 9) | `lib/focus-error.ts`; verified: empty HbA1c submit → focus on `#hba1c` |
| 8 | Status messages announced | 4.1.3 | Pass | Step-1 result card is `aria-live="polite"` and receives focus; progress text is `role="status"`; alerts use `role="alert"` |
| 9 | Text contrast ≥ 4.5:1 | 1.4.3 | Pass | 16 colour pairs computed; lowest is small grey notes (slate-500 on white) at 4.77:1; primary button text 5.39:1 |
| 10 | Page language set | 3.1.1 | Pass | `<html lang="en">` |
| 11 | Heading structure | 1.3.1, 2.4.6 | Pass | Report: one H1, ten H2 sections in order; each section `aria-labelledby` its heading |
| 12 | Landmarks | 1.3.1 | Pass | `header`, `main#main`, `footer`; report sections are labelled regions |
| 13 | Reflow at 360 px, no horizontal scroll | 1.4.10 | Pass | Landing, step 1 and the full report: `scrollWidth` = 360 in a 360 px frame |
| 14 | Images have text alternatives | 1.1.1 | Pass (n/a) | No content images; decorative spinner and step bar are `aria-hidden` |
| 15 | Screen-reader pass (VoiceOver) | — | Not done | Recommended before public launch; not required for the submission |

## Known limitations
- The screen-reader pass (row 15) was not performed; the structural checks above are what a screen
  reader relies on, but an actual VoiceOver/NVDA run is still advised.
- The browser automation could not shrink Chrome below ~1,000 px; reflow was measured in a 360 px
  same-origin frame instead, which applies the same CSS breakpoints.
