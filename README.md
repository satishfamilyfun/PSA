# PSA SDLC Agents

SDLC agents (BA, QA and a four-agent developer team) for the **Photo Sorting App** project, built on Claude Code with the Atlassian Rovo MCP server, custom skills, hooks and a custom MCP tool. Each agent takes a Jira ticket key, gathers context from the ticket, comments, attachments, linked tickets and the Confluence knowledge base, and performs its role.

Design: [docs/agent-system-design.md](docs/agent-system-design.md)

## Repository layout
| Path | Contents |
|---|---|
| `kb/` | Full product design (11 pages), published to Confluence |
| `seed/` | Scripts that create the Jira backlog, publish the KB and reset the demo |
| `assets/` | Ticket attachments (wireframe, mockup, sample EXIF output) |
| `common/` | Shared Jira/Confluence client |
| `tests/` | Offline tests for the seed scripts |
| `docs/` | Agent system design |
| `.claude/` | Subagents, skills, hooks, slash commands, permissions |
| `tools/` | Custom `psa` MCP server (ticket bundle with attachments) |
| `evals/` | Expected findings per demo scenario and the scoring script |
| `app/` | Photo Sorting App code written by the developer agents (Python core, React UI) |
| `metrics/` | Metrics report and dashboard, model benchmark, pricing table |
| `CLAUDE.md` | Project memory loaded by Claude Code |

## Setup (Windows PowerShell)

### 1. Unzip and create a virtual environment
```powershell
cd D:\photoapp
# unzip psa-sdlc-agents.zip here so that README.md is directly in D:\photoapp
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
If activation fails with a "running scripts is disabled" error, run this once and try again:
```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned
```

### 2. Add your credentials
```powershell
Copy-Item .env.example .env
notepad .env
```
Fill in `ATLASSIAN_EMAIL` and `ATLASSIAN_API_TOKEN`, save and close. `.env` is in `.gitignore` and must never be committed.

### 3. Run the offline tests
```powershell
pytest
```
Expect `76 passed`.

### 4. Seed Jira, then Confluence (order matters)
```powershell
python -m seed.seed_jira
python -m seed.seed_confluence
```
The Jira script prints every ticket it creates and the three demo target keys. The Confluence script replaces story placeholders in the KB with the real Jira keys.

### 5. Check in the browser
- Jira PSA board: 8 epics and 21 stories; the import wizard, face labeling and EXIF stories have attachments.
- Open the face labeling story: it should show "is blocked by" the face clustering story.
- Confluence space PSA: 11 pages, starting with "Product Vision and Roadmap".

### 6. Push to GitHub
```powershell
git init
git branch -M main
git remote add origin https://github.com/satishfamilyfun/PSA.git
git pull origin main --allow-unrelated-histories   # only if the repo already has files
git add .
git commit -m "chore: add seed data, knowledge base and agent system design"
git push -u origin main
```

## Running the agents in Claude Code

### 1. Start Claude Code from the activated virtual environment
```powershell
cd D:\photoapp
.\.venv\Scripts\Activate.ps1
claude
```
Starting from the activated environment matters: the hooks and the `psa` MCP server run with `python`, which must be the virtual environment's Python.

On first start, accept the workspace trust prompt and approve the project MCP server `psa`.

### 2. Check the setup
- `/mcp` shows `atlassian` and `psa` as connected.
- `/agents` lists `ba-agent`, `qa-agent` and the four developer agents.

### 3. Run the demo scenarios
Use the keys printed by `seed_jira` (also in `seed_state.json`: S3, S6 and S4).
```
/ba-review PSA-<S3 key>     Scenario 1: scope conflict
/ba-review PSA-<S6 key>     Scenario 2: dependency awareness
/qa-design PSA-<S4 key>     Scenario 3: QA test design
```
Claude Code asks for approval before each Jira write. Reports go to `runs/reports/`, traces to `runs/traces/`, and every tool call to `runs/audit.jsonl`.

### 4. Score a run
In a second PowerShell window (venv active):
```powershell
python -m evals.check_run PSA-<key> ba
```

### Guardrails you can demonstrate
Ask the agent to "also close the ticket" or "create a follow-up ticket". The BA and QA agents do not have those tools. If the main session tries, Claude Code asks for approval first, and even when approved the guard hook blocks it: tickets can be created only as sub-tasks during `/dev-implement`, and only those sub-tasks may change status. The block appears in `runs/audit.jsonl` and the trace.

## Developer team and metrics

### One-time setup
```powershell
winget install GitHub.cli        # then: gh auth login
winget install OpenJS.NodeJS.LTS # then open a new terminal
npm --prefix app/ui install
python -m pytest app -q          # 2 baseline tests
npm --prefix app/ui test         # 1 baseline test
```
In Claude Code, run `/model` and check whether Opus is offered. If not, change `model: opus` to
`model: sonnet` in `.claude/agents/senior-developer.md` (keep `effort: high`).
Do not set `CLAUDE_CODE_SUBAGENT_MODEL`; each agent's model comes from its file.

### Run the team on a ready story
```
/dev-implement PSA-<S4 key> including a small photo metadata panel for the gallery detail view (PSA-<S8 key>)
```
The senior developer plans and creates Jira sub-tasks, specialists build in parallel, the senior reviews,
rework loops run at most twice, tests run, then commit, push and PR (each with your approval).
The story gets a metrics comment at the end.

### Metrics
| What | How |
|---|---|
| Per-run tokens, cost, time, tool calls, errors | Recorded automatically by the `collect_metrics` hook |
| Story summary + dashboard | `python -m metrics.report --story PSA-<key>` then open `runs/metrics/dashboard.html` |
| Model right-sizing benchmark | `python -m metrics.benchmark` (same task on Haiku, Sonnet, Opus; scored by hidden tests) |
| Cross-check token totals | `npx ccusage` (optional) |

Cost is the API-equivalent estimate from `metrics/pricing.json` (edit to current list prices); on Pro you pay a flat fee.

## Resetting the demo
Before each rehearsal and before recording:
```powershell
python -m seed.reset_demo
```
This restores every story's description and labels and removes comments added after seeding.

## Troubleshooting
| Symptom | Fix |
|---|---|
| `401` errors | Check the email and token in `.env`; the token must be an unscoped "Create API token" token |
| `Project PSA not found` | Check `JIRA_PROJECT_KEY` and that your account can see the project |
| `seed_state.json exists` | The project is already seeded; use `reset_demo`, or `--force` to seed again |
| Stories are not under epics | Your project type rejected the parent link; stories are still created and the demo works |
| Hook error "python not found" | Start `claude` from a terminal where the virtual environment is active |
| Dashboard charts empty | It needs internet for Chart.js (cdnjs); data tables still show |
| A developer agent is blocked writing a file | Expected if outside its folder; see `runs/audit.jsonl` |
| `psa` server not connected | Run `/mcp`, check its error; usually missing `.env` values or `pip install -r requirements.txt` not run |
