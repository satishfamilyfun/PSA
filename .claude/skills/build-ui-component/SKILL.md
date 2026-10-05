---
name: build-ui-component
description: Build accessible, kid-friendly React + TypeScript components for the PSA app with Vitest tests, based on mockups and the Feature Design Specs. Use for any UI task.
---

# Build a UI component

## Structure
- One component per file in `app/ui/src/components/<Name>.tsx`, a named export, typed props.
- Test file next to it: `<Name>.test.tsx` using `@testing-library/react` and Vitest.
- Inline styles are fine (no CSS framework installed). Do not add packages.

## Usability rules (Personas page: kids 10+, non-technical adults)
- Plain words: "Taken on", "Place", not "DateTimeOriginal" or "GPS".
- Text 16px or larger, buttons at least 44px tall, clear focus outline.
- Show friendly text for missing data ("Date unknown", "No location saved"), never blank, null or NaN.
- Flagged data is explained, for example a suspect date shows "This date may be wrong".
- Use semantic elements and labels (`dl`/`dt`/`dd` for details, `aria-label` on icon-only buttons).

## Tests
Cover: full data renders, each missing field shows its friendly text, flags show their explanation,
and one accessibility check (a role or label query). Run `npm --prefix app/ui test`.
