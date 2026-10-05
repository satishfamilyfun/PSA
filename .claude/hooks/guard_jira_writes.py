"""PreToolUse hook for Atlassian tools. Exit code 2 blocks the call and tells Claude why.

Rules (defence in depth on top of the permission rules):
  1. Destructive, generic and Confluence write tools are always blocked.
  2. Creating issues: only Jira sub-tasks under the active story, only during /dev-implement.
  3. Status changes: only sub-tasks listed in the active story's plan, only during /dev-implement.
  4. Comments and edits: only the active ticket (and, for dev runs, its planned sub-tasks).
  5. Comments may be added, never edited.
  6. editJiraIssue may change description and labels (BA) or labels only (QA, dev).

Target tickets are read only from identifying fields (issue key, parent, ...). Free text such as a
comment body, description or summary is ignored, because agents legitimately cite other tickets
there ("blocked by PSA-9") without writing to them.
"""
import json
import re
import sys

from _hooklib import PROJECT_KEY, active_ticket, audit, plan_subtasks, read_event, short

ALWAYS_BLOCKED = {
    "executeDestructive": "destructive operations are never allowed",
    "executeWrite": "generic writes bypass review; use the named Jira tools instead",
    "createConfluenceContent": "the knowledge base is read-only for agents",
    "updateConfluenceContent": "the knowledge base is read-only for agents",
    "addGraphContext": "Teamwork Graph is not used in this project",
}
WRITE_TOOLS = {"addOrEditJiraIssueComment", "editJiraIssue", "createJiraIssue", "transitionJiraIssue"}
ALLOWED_FIELDS = {"ba": {"description", "labels"}, "qa": {"labels"}, "dev": {"labels"}}
KEY_RE = re.compile(r"\b[A-Z][A-Z0-9]+-\d+\b")
TEXT_FIELDS = {"body", "commentbody", "comment", "description", "summary", "text", "content",
               "value", "title", "environment", "adf", "markdown"}


def strip_text(obj):
    """The request without free-text fields; JSON passed as a string is parsed first."""
    if isinstance(obj, str) and obj.strip().startswith(("{", "[")):
        try:
            obj = json.loads(obj)
        except json.JSONDecodeError:
            return obj
    if isinstance(obj, dict):
        return {k: strip_text(v) for k, v in obj.items() if k.lower() not in TEXT_FIELDS}
    if isinstance(obj, list):
        return [strip_text(v) for v in obj]
    return obj


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
    raw = json.dumps(strip_text(tool_input))  # identifying fields only, never free text
    keys = set(KEY_RE.findall(raw))
    active = active_ticket()
    story, role = active.get("key"), active.get("role")

    if any(not k.startswith(PROJECT_KEY + "-") for k in keys):
        block(tool_name, f"writes are limited to project {PROJECT_KEY}")

    if tool == "createJiraIssue":
        if role != "dev" or not story:
            block(tool_name, "agents may create tickets only as sub-tasks during /dev-implement")
        if not re.search(r"sub-?task", raw, re.IGNORECASE):
            block(tool_name, "only issues of type Subtask may be created")
        if keys != {story}:
            block(tool_name, f"sub-tasks may only be created under {story}")
    else:
        if not keys:
            block(tool_name, "could not find a ticket key in the request")
        allowed = {story} if story else set()
        if role == "dev" and story:
            allowed |= plan_subtasks(story)
        if story and not keys <= allowed:
            block(tool_name, f"this run may only write to {', '.join(sorted(allowed))}, "
                             f"not {', '.join(sorted(keys - allowed))}")

    if tool == "transitionJiraIssue" and (role != "dev" or story in keys):
        block(tool_name, "only planned sub-tasks may change status; story status is left to people")

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
        allowed_fields = ALLOWED_FIELDS.get(role, ALLOWED_FIELDS["ba"])
        changed = set((fields or {}).keys())
        if changed - allowed_fields:
            block(tool_name, f"may only change {sorted(allowed_fields)}, not {sorted(changed - allowed_fields)}")

    audit({"event": "write_allowed", "tool": tool_name, "keys": sorted(keys), "input": short(tool_input)})
sys.exit(0)
