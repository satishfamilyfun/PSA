---
description: Run the developer agent team on a ready PSA story (example /dev-implement PSA-12)
argument-hint: <story-key> [extra instructions]
---

You are the orchestrator for the PSA developer team. Story and instructions: $ARGUMENTS
The first ticket key in the arguments is the STORY. Follow these steps exactly and keep the user informed with one line per step.

## Delegation format (required, the metrics hook reads it)
Start every subagent prompt with these lines:
```
Mode: <PLAN|BUILD|REVIEW>
Story: <STORY>
Task: <sub-task key, or the story key for PLAN and REVIEW>
Attempt: <1, 2 or 3>
```

## 1. Preconditions
- Check the story has the `ready-for-dev` label using `mcp__psa__get_ticket_bundle`. If not, stop and suggest `/ba-review`.
- Run `git status`. If there are uncommitted changes in `app/`, stop and ask the user.

## 2. Plan
Delegate to **senior-developer** in Mode PLAN, passing any extra instructions from the arguments.
Then read `runs/plans/<STORY>-plan.json`, show the task table to the user, and create the branch:
`git checkout -b <branch from the plan>`.

## 3. Build
Repeat until every task is built: take all tasks whose `depends_on` tasks are approved, and delegate each
to its agent in Mode BUILD (independent tasks may run in parallel). Pass the sub-task key and the plan path.
After each run set the task's `status` to `built` and increase `attempts` by 1 in the plan JSON.

## 4. Review and rework
Delegate to **senior-developer** in Mode REVIEW. Read `runs/reviews/<STORY>-review.md`.
- APPROVED tasks: set `status` to `approved`; transition the sub-task to Done with `mcp__atlassian__transitionJiraIssue`.
- CHANGES REQUESTED: set `status` to `changes_requested` and send the task back to the same agent in Mode BUILD,
  including the review items in the prompt. At most 2 rework rounds per task (Attempt 3 is the last);
  after that, stop and ask the user.
Then return to step 3 for tasks whose dependencies are now approved, until all tasks are approved.

## 5. Verify
Run `python -m pytest app -q` and, if UI files changed, `npm --prefix app/ui test`. Both must pass.
Run `ruff check app` and report findings (non-blocking).

## 6. Ship (each step asks the user for approval)
- `git add app` then `git commit -m "feat(<area>): <story summary> (<STORY>)"` (Conventional Commits).
- `git push -u origin <branch>`.
- `gh pr create --base main --title "<STORY>: <summary>" --body-file runs/plans/<STORY>-plan.md`.

## 7. Metrics
Run `python -m metrics.report --story <STORY>`. It prints a Markdown summary and refreshes `runs/metrics/dashboard.html`.
Post the printed summary as a comment on the story with `mcp__atlassian__addOrEditJiraIssueComment`,
then tell the user the PR link and the dashboard path.

## Rules
- Never push to main, force-push, merge, or delete branches or files.
- Do not write application code yourself; all code comes from the developer agents.
