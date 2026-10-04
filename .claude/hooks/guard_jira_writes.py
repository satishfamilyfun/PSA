"""PreToolUse hook for Atlassian tools. Exit code 2 blocks the call and tells Claude why.

Rules (defence in depth on top of the permission rules):
  1. Destructive, generic and Confluence write tools are always blocked.
  2. Creating issues: only Jira sub-tasks under the active story, only during /dev-implement.
  3. Status changes: only the story's sub-tasks, only during /dev-implement.
  4. Comments and edits: only the active ticket (and, for dev runs, its sub-tasks).
  5. Comments may be added, never edited.
  6. editJiraIssue may change description and labels (BA) or labels only (QA, dev).

The write target comes from issueIdOrKey (parent for createJiraIssue); keys cited in body text
are just references. A dev run's sub-tasks are those both listed in the plan and seen created
under the story by audit_log.py, so editing the plan alone cannot widen what may be written.
"""
import json
import re
import sys

from _hooklib import PROJECT_KEY, active_ticket, audit, created_subtasks, plan_subtasks, read_event, short

ALWAYS_BLOCKED = {
    "executeDestructive": "destructive operations are never allowed",
    "executeWrite": "generic writes bypass review; use the named Jira tools instead",
    "createConfluenceContent": "the knowledge base is read-only for agents",
    "updateConfluenceContent": "the knowledge base is read-only for agents",
    "addGraphContext": "Teamwork Graph is not used in this project",
}
WRITE_TOOLS = {"addOrEditJiraIssueComment", "editJiraIssue", "createJiraIssue", "transitionJiraIssue"}
ALLOWED_FIELDS = {"ba": {"description", "labels"}, "qa": {"labels"}, "dev": {"labels"}}
KEY_RE = re.compile(r"[A-Z][A-Z0-9]+-\d+")


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
    active = active_ticket()
    story, role = active.get("key"), active.get("role")

    if tool == "createJiraIssue":
        if role != "dev" or not story:
            block(tool_name, "agents may create tickets only as sub-tasks during /dev-implement")
        if str(tool_input.get("projectKey", "")).strip().upper() != PROJECT_KEY:
            block(tool_name, f"writes are limited to project {PROJECT_KEY}")
        issue_type = str(tool_input.get("issueType") or tool_input.get("issueTypeName") or "").strip()
        if not re.fullmatch(r"sub-?task", issue_type, re.IGNORECASE):
            block(tool_name, "only issues of type Subtask may be created")
        target = str(tool_input.get("parent", "")).strip().upper()
        if target != story:
            block(tool_name, f"sub-tasks may only be created under {story}")
    else:
        target = str(tool_input.get("issueIdOrKey", "")).strip().upper()
        if not KEY_RE.fullmatch(target):
            block(tool_name, "issueIdOrKey must be a ticket key such as PSA-3")
        if not target.startswith(PROJECT_KEY + "-"):
            block(tool_name, f"writes are limited to project {PROJECT_KEY}")
        allowed = {story} if story else set()
        if role == "dev" and story:
            allowed |= plan_subtasks(story) & created_subtasks(story)
        if story and target not in allowed:
            block(tool_name, f"this run may only write to {', '.join(sorted(allowed))}, not {target}")

    if tool == "transitionJiraIssue" and (role != "dev" or target == story):
        block(tool_name, "only the story's sub-tasks may change status; story status is left to people")

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

    audit({"event": "write_allowed", "tool": tool_name, "key": target, "input": short(tool_input)})
sys.exit(0)
