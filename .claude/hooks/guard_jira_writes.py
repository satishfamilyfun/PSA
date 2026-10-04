"""PreToolUse hook for Atlassian tools. Exit code 2 blocks the call and tells Claude why.

Rules (defence in depth on top of the permission deny list):
  1. Destructive, generic and out-of-role tools are always blocked.
  2. Writes must target the PSA project and, during a run, only the ticket under review.
  3. Comments may be added, never edited (human comments stay untouched).
  4. editJiraIssue may change description and labels only; the QA agent may change labels only.
"""
import json
import re
import sys

from _hooklib import PROJECT_KEY, active_ticket, audit, read_event, short

ALWAYS_BLOCKED = {
    "executeDestructive": "destructive operations are never allowed",
    "executeWrite": "generic writes bypass review; use the named Jira tools instead",
    "createJiraIssue": "agents must not create tickets",
    "transitionJiraIssue": "status changes are left to people",
    "createConfluenceContent": "the knowledge base is read-only for agents",
    "updateConfluenceContent": "the knowledge base is read-only for agents",
    "addGraphContext": "Teamwork Graph is not used in this project",
}
WRITE_TOOLS = {"addOrEditJiraIssueComment", "editJiraIssue"}
ALLOWED_FIELDS = {"ba": {"description", "labels"}, "qa": {"labels"}}


def block(tool: str, reason: str) -> None:
    audit({"event": "blocked", "tool": tool, "reason": reason})
    print(f"Blocked by guard_jira_writes: {reason}", file=sys.stderr)
    sys.exit(2)


event = read_event()
tool_name = event.get("tool_name", "")
tool = tool_name.split("__")[-1]
tool_input = event.get("tool_input", {}) or {}

if tool in ALWAYS_BLOCKED:
    block(tool_name, ALWAYS_BLOCKED[tool])

if tool in WRITE_TOOLS:
    keys = set(re.findall(r"\b[A-Z][A-Z0-9]+-\d+\b", json.dumps(tool_input)))
    if not keys:
        block(tool_name, "could not find a ticket key in the request")
    if any(not k.startswith(PROJECT_KEY + "-") for k in keys):
        block(tool_name, f"writes are limited to project {PROJECT_KEY}")
    active = active_ticket()
    if active.get("key") and keys != {active["key"]}:
        block(tool_name, f"this run may only write to {active['key']}, not {', '.join(sorted(keys))}")

    if tool == "addOrEditJiraIssueComment" and any(
            k.lower() in ("commentid", "comment_id") for k in tool_input):
        block(tool_name, "editing existing comments is not allowed; add a new comment instead")

    if tool == "editJiraIssue":
        fields = tool_input.get("fields")
        if isinstance(fields, str):
            try:
                fields = json.loads(fields)
            except json.JSONDecodeError:
                fields = {}
        allowed = ALLOWED_FIELDS.get(active.get("role"), ALLOWED_FIELDS["ba"])
        changed = set((fields or {}).keys())
        if changed - allowed:
            block(tool_name, f"may only change {sorted(allowed)}, not {sorted(changed - allowed)}")

    audit({"event": "write_allowed", "tool": tool_name, "keys": sorted(keys),
           "input": short(tool_input)})
sys.exit(0)
