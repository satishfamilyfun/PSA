# PSA SDLC Agents - project memory

## What this repo is
SDLC agents for the **Photo Sorting App (PSA)**, a Windows desktop app for organizing family photos.
The app itself is designed (Confluence) but not implemented; this repo holds the agents that work on its backlog.

## Where things are
- **Jira**: project `PSA` on satishfamilyfun.atlassian.net (team-managed). 8 epics, 21 stories across 3 phases.
- **Confluence**: space `PSA`, 11 design pages. Source files in `kb/`.
- **Agents**: `.claude/agents/` (ba-agent, qa-agent). Entry points: `/ba-review <KEY>`, `/qa-design <KEY>`.
- **Skills**: `.claude/skills/`. **Hooks**: `.claude/hooks/`. **Ticket context tool**: `tools/psa_tools_mcp.py` (MCP server `psa`).
- **Outputs**: reports in `runs/reports/`, traces in `runs/traces/`, audit log `runs/audit.jsonl`.

## Product rules every agent must respect
- Phases: Phase 1 library MVP, Phase 2 smart library, Phase 3 sharing. Features are sequenced, never cancelled.
- Originals are never changed; the app works on copies.
- Nothing is permanently deleted (Phase 2 removals go to the Recycle Bin).
- Only 10-15 tracked people; all other faces are Unknown.
- Users include non-technical adults and kids aged 10 and up.

## Working conventions
- Get ticket context with `mcp__psa__get_ticket_bundle` first; use Atlassian MCP tools for Confluence and for writing back.
- Write only to the ticket under review. Never create tickets, change status, edit existing comments or edit Confluence.
- Prefer few, targeted Confluence reads over reading every page (usage limits on the Pro plan).
- Ticket keys look like `PSA-12`. Seed IDs like `S3` appear only in `seed/` scripts.

## Commands
- Tests: `pytest`
- Reset demo tickets: `python -m seed.reset_demo`
- Score a run: `python -m evals.check_run <KEY> <ba|qa>`
