---
name: review-code
description: Review code produced by PSA developer agents against the plan, the story's acceptance criteria and QA scenarios, and the engineering standards, then record an APPROVED or CHANGES REQUESTED verdict per task. Use for code review.
---

# Review code

For each task in `runs/plans/<KEY>-plan.json` with status `built`:

1. Read the task's result file `runs/tasks/<SUBTASK>-result.md` and every file it changed (`git diff` helps).
2. Run `python -m pytest app -q` (and `npm --prefix app/ui test` for UI tasks). Failing tests = CHANGES REQUESTED.
3. Check, in this order:
   - **Correctness**: each acceptance item in the task is met; edge cases from the QA scenarios are handled
     (no EXIF, no GPS, HEIC, suspicious dates such as a scanner's 1980 default).
   - **Safety principles**: originals never modified; nothing deleted.
   - **Standards**: type hints and docstrings on public functions, clear names, no dead code, tests for new behaviour.
   - **Scope**: the agent changed only its own files and did only its task.
4. Verdict:
   - APPROVED: no blocking issues. Minor suggestions may be listed as "non-blocking".
   - CHANGES REQUESTED: list each issue as `file:line - problem - required change`. Be specific enough
     that the same agent can fix it without asking.

## Output: runs/reviews/<KEY>-review.md
```
# Code review: <KEY>
| Task | Sub-task | Agent | Verdict | Issues |
|---|---|---|---|---|
## Details per task
## Tests run (command and result)
```
Count blocking issues per task honestly: the metrics dashboard reports first-pass approval rate.
