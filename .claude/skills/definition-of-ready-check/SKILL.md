---
name: definition-of-ready-check
description: Evaluate a Jira story against the PSA Definition of Ready from the BA Standards page and produce a pass/fail table with evidence. Use when refining or reviewing a story before development.
---

# Definition of Ready check

Evaluate each criterion and record Pass, Fail or Partial with one line of evidence.

| # | Criterion | How to check |
|---|-----------|--------------|
| 1 | User story format with a named persona | "As a [persona], I want..., so that..." and the persona exists on the Personas page |
| 2 | Testable acceptance criteria incl. edge and error cases | Given/When/Then present; QA could test each without asking |
| 3 | Matches its roadmap phase | Compare with the Product Vision and Roadmap page; work belonging to another phase must point to the right story |
| 4 | Blockers Done or risk accepted | Linked "is blocked by" tickets and their status |
| 5 | Open questions resolved | Questions in this ticket's comments and in blockers' comments |
| 6 | Attachments match the description | Every option, field and number in wireframes or mockups is reflected in the text |

## Verdict
- All six Pass: recommend label `ready-for-dev`.
- Any Fail or Partial: recommend label `needs-clarification` and list what is needed to pass.

## Output
```
| # | Criterion | Result | Evidence |
|---|-----------|--------|----------|
| 1 | Story format and persona | Fail | No persona; description starts "As a family member I want to import..." without a benefit |
```
