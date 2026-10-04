"""PostToolUse hook: append every MCP tool call to runs/audit.jsonl, and record sub-tasks
created during /dev-implement so guard_jira_writes can limit later writes to them."""
import json
import re

from _hooklib import active_ticket, audit, read_event, record_subtask, short

# The new issue's key in the tool response, e.g. "key": "PSA-30" (possibly JSON-escaped inside text content).
NEW_KEY_RE = re.compile(r'key\W{0,6}([A-Z][A-Z0-9]+-\d+)')

event = read_event()
response = event.get("tool_response")
failed = isinstance(response, dict) and bool(response.get("isError") or response.get("error"))
active = active_ticket()
audit({
    "event": "tool_call",
    "ticket": active.get("key"),
    "tool": event.get("tool_name"),
    "input": short(event.get("tool_input", {})),
    "ok": not failed,
})

if (event.get("tool_name", "").endswith("__createJiraIssue") and not failed
        and active.get("role") == "dev" and active.get("key")):
    created = [k for k in NEW_KEY_RE.findall(json.dumps(response, default=str)) if k != active["key"]]
    if created:
        record_subtask(active["key"], created[0])
        audit({"event": "subtask_recorded", "story": active["key"], "key": created[0]})
