"""SubagentStop hook: write a Markdown trace of the run (evidence for reviewers)."""
import json
from collections import Counter

from _hooklib import AUDIT, RUNS, active_ticket, now, read_event

event = read_event()
active = active_ticket()
key, started = active.get("key", "unknown"), active.get("started_at", "")
agent = event.get("agent_type") or active.get("role", "agent")

entries = []
if AUDIT.exists():
    for line in AUDIT.read_text(encoding="utf-8").splitlines():
        try:
            item = json.loads(line)
        except json.JSONDecodeError:
            continue
        if item.get("ts", "") >= started:
            entries.append(item)

calls = Counter(e["tool"] for e in entries if e.get("event") == "tool_call")
writes = [e for e in entries if e.get("event") == "write_allowed"]
blocked = [e for e in entries if e.get("event") == "blocked"]
report = RUNS / "reports" / f"{key}-{active.get('role', 'agent')}.md"

call_lines = [f"- {t}: {n}" for t, n in calls.most_common()] or ["(none)"]
write_lines = [f"- {w['tool']} on {', '.join(w['keys'])}" for w in writes] or ["(none)"]
block_lines = [f"- {b['tool']}: {b['reason']}" for b in blocked] or ["(none)"]

lines = [f"# Run trace: {agent} on {key}", f"- Started: {started}", f"- Finished: {now()}",
         f"- Report: {report.name if report.exists() else '(no report written)'}",
         "", "## Tool calls", *call_lines,
         "", "## Jira writes approved by guard", *write_lines,
         "", "## Blocked actions", *block_lines]

(RUNS / "traces").mkdir(parents=True, exist_ok=True)
stamp = now().replace(":", "").replace("-", "")[:15]
(RUNS / "traces" / f"{stamp}-{agent}-{key}.md").write_text("\n".join(lines), encoding="utf-8")
