# PSA SDLC Agents - project memory

## What this repo is
SDLC agents for the **Photo Sorting App (PSA)**, a Windows desktop app for organizing family photos.
The app itself is designed (Confluence) but not implemented; this repo holds the agents that work on its backlog.

## Where things are
- **Jira**: project `PSA` on satishfamilyfun.atlassian.net (team-managed). 8 epics, 21 stories across 3 phases.
- **Confluence**: space `PSA`, 11 design pages. Source files in `kb/`.
- **Agents**: `.claude/agents/`. BA and QA: `/ba-review <KEY>`, `/qa-design <KEY>`.
  Developer team: senior-developer (Opus), database-developer and ui-developer (Sonnet), junior-developer (Haiku),
  orchestrated by `/dev-implement <KEY>`.
- **App code**: `app/` (Python core, React UI in `app/ui`). Folder ownership per agent is in `app/README.md`
  and enforced by `.claude/hooks/guard_code_writes.py`.
- **Skills**: `.claude/skills/`. **Hooks**: `.claude/hooks/`. **Ticket context tool**: `tools/psa_tools_mcp.py` (MCP server `psa`).
- **Outputs**: reports `runs/reports/`, plans `runs/plans/`, task results `runs/tasks/`, reviews `runs/reviews/`,
  traces `runs/traces/`, audit log `runs/audit.jsonl`, metrics `runs/metrics/` (agent_runs.jsonl, benchmark.jsonl, dashboard.html).

## Product rules every agent must respect
- Phases: Phase 1 library MVP, Phase 2 smart library, Phase 3 sharing. Features are sequenced, never cancelled.
- Originals are never changed; the app works on copies.
- Nothing is permanently deleted (Phase 2 removals go to the Recycle Bin).
- Only 10-15 tracked people; all other faces are Unknown.
- Users include non-technical adults and kids aged 10 and up.

## Working conventions
- Get ticket context with `mcp__psa__get_ticket_bundle` first; use Atlassian MCP tools for Confluence and for writing back.
- Write only to the ticket under review. Never create tickets, change status, edit existing comments or edit Confluence.
  Only exception: during `/dev-implement` the senior developer creates sub-tasks under the story, and the orchestrator
  may change those sub-tasks' status. The story's own status is always left to people.
- Prefer few, targeted Confluence reads over reading every page (usage limits on the Pro plan).
- Ticket keys look like `PSA-12`. Seed IDs like `S3` appear only in `seed/` scripts.

## Developer conventions
- Python 3.11+, type hints and docstrings on public functions, pytest tests for new behaviour.
- Schema changes are new numbered migrations in `app/core/db/migrations/`; never edit an applied one.
- Branches `feature/<KEY>-short-name`; Conventional Commits; only the orchestrator runs git write commands.
- Delegation prompts start with `Mode:`, `Story:`, `Task:`, `Attempt:` lines (the metrics hook reads them).

## Commands
- Tests: `pytest`
- Reset demo tickets: `python -m seed.reset_demo`
- Score a run: `python -m evals.check_run <KEY> <ba|qa>`
- App tests: `python -m pytest app -q` and `npm --prefix app/ui test`
- Metrics: `python -m metrics.report [--story <KEY>]`; model benchmark: `python -m metrics.benchmark`
