---
name: plan-implementation
description: Turn a ready PSA story into an implementation plan with small tasks assigned to the right developer agent (senior, database, UI, junior), dependencies and acceptance notes, saved as JSON and Markdown. Use when planning development of a story.
---

# Plan implementation

## Inputs to use
- The story's acceptance criteria and any QA Gherkin scenarios in its comments: these define "done".
- Architecture Overview (components), Data Model (tables, columns), Engineering Standards.
- The existing code in `app/` (read it; do not plan work that already exists).

## Assign work by skill and risk
| Agent | Gets | Model tier |
|---|---|---|
| database-developer | Migrations, columns, queries, repository functions | Sonnet |
| senior-developer | Complex or risky logic (parsing, edge-case-heavy code) | Opus |
| ui-developer | React components | Sonnet |
| junior-developer | Small helpers with exact signatures, unit tests for code already specified | Haiku |

Give the junior developer a task only when you can state the exact function signature or test list.

## Task rules
- One task = one agent, one run, roughly under 150 lines of change.
- Each task names the files it touches; two tasks never edit the same file.
- `depends_on` lists task ids that must be approved first. Tasks without dependencies can run in parallel.
- `acceptance` lists checks the reviewer will apply, mapped to story acceptance criteria (AC1, AC2...).

## Output 1: runs/plans/<KEY>-plan.json
```json
{
  "story": "PSA-12",
  "branch": "feature/PSA-12-exif-metadata",
  "summary": "Extract date taken and GPS during import and store them.",
  "tasks": [
    {"id": "T1", "agent": "database-developer", "title": "Add EXIF columns to photos",
     "subtask_key": null, "depends_on": [], "files": ["app/core/db/migrations/002_exif_metadata.sql"],
     "acceptance": ["AC1: date_taken column", "AC2: gps_lat and gps_lon as REAL"],
     "status": "planned", "attempts": 0}
  ]
}
```
`status` values: planned, built, changes_requested, approved. `attempts` counts build runs (the orchestrator updates it).

## Output 2: runs/plans/<KEY>-plan.md
A short readable version: goal, task table (id, agent, title, depends on), risks, out of scope.
