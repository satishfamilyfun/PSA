"""PostToolUse hook: append every MCP tool call to runs/audit.jsonl."""
from _hooklib import active_ticket, audit, read_event, short

event = read_event()
response = event.get("tool_response")
failed = isinstance(response, dict) and bool(response.get("isError") or response.get("error"))
audit({
    "event": "tool_call",
    "ticket": active_ticket().get("key"),
    "tool": event.get("tool_name"),
    "input": short(event.get("tool_input", {})),
    "ok": not failed,
})
