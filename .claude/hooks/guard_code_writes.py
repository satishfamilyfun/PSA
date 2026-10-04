"""PreToolUse hook for file writes and shell commands. Exit code 2 blocks the call.

  1. Each subagent may write only inside the folders it owns (see OWNERSHIP).
  2. Dangerous commands are blocked for everyone: force push, push to main, hard reset,
     recursive deletes, merges.
  3. Subagents may not run git write commands, install packages or redirect output into files;
     the orchestrator (main session) handles git.
"""
import re
import sys

from _hooklib import PROJECT, PROTECTED, audit, read_event, short

OWNERSHIP = {
    "senior-developer": ["app/core/metadata/", "runs/"],
    "database-developer": ["app/core/db/", "app/tests/test_db_", "runs/"],
    "ui-developer": ["app/ui/src/", "runs/"],
    "junior-developer": ["app/core/utils/", "app/tests/", "runs/"],
    "ba-agent": ["runs/"],
    "qa-agent": ["runs/"],
}
DEFAULT_SUBAGENT = ["runs/"]  # any other subagent, including built-in ones

ALWAYS_BLOCKED_CMDS = [
    (r"git\s+push\b.*(\s--force\b|\s-f\b|--force-with-lease)", "force push is not allowed"),
    (r"git\s+push\b.*\b(origin\s+)?(main|master)\b", "pushing to main is not allowed; push a feature branch"),
    (r"git\s+reset\s+--hard", "hard reset is not allowed"),
    (r"git\s+(clean|branch\s+-D)\b", "deleting files or branches is not allowed"),
    (r"(\bgit\s+merge\b|\bgh\s+pr\s+merge\b)", "merging is left to people"),
    (r"\brm\s+-[a-zA-Z]*r|\bRemove-Item\b|\brmdir\b|\brd\s+/s|\bdel\s", "deleting files is not allowed"),
]
SUBAGENT_BLOCKED_CMDS = [
    (r"\bgit\s+(commit|push|checkout|switch|rebase|stash|tag)\b", "git write commands are done by the orchestrator"),
    (r"\b(npm|pnpm|yarn)\s+(install|i|add|remove)\b|\bpip\s+install\b", "installing packages is not allowed"),
    (r"(^|[^0-9&>\-])>{1,2}\s*[\w./\\]|\b(Set-Content|Out-File|tee)\b",
     "write files with the Write or Edit tool, not shell redirection"),
]


def block(agent: str, tool: str, reason: str) -> None:
    audit({"event": "blocked", "tool": tool, "agent": agent or "main", "reason": reason})
    print(f"Blocked by guard_code_writes: {reason}", file=sys.stderr)
    sys.exit(2)


def relative(path_str: str) -> str:
    """Project-relative POSIX path in lower case (works for Windows and POSIX paths)."""
    norm = lambda p: p.replace("\\", "/").rstrip("/").lower()
    path, root = norm(path_str), norm(str(PROJECT))
    return path[len(root):].lstrip("/") if path.startswith(root) else path


event = read_event()
tool = event.get("tool_name", "")
agent = event.get("agent_type") or ""
tool_input = event.get("tool_input", {}) or {}

if tool == "Bash":
    command = tool_input.get("command", "")
    for pattern, reason in ALWAYS_BLOCKED_CMDS:
        if re.search(pattern, command, re.IGNORECASE):
            block(agent, tool, f"{reason} ({short(command, 80)})")
    if agent:
        for pattern, reason in SUBAGENT_BLOCKED_CMDS:
            if re.search(pattern, command, re.IGNORECASE):
                block(agent, tool, f"{reason} ({short(command, 80)})")
    sys.exit(0)

path = tool_input.get("file_path") or tool_input.get("notebook_path") or ""
if path and relative(path).startswith(PROTECTED):
    block(agent, tool, f"{relative(path)} is written only by the hooks")
if agent and path:
    rel = relative(path)
    allowed = OWNERSHIP.get(agent, DEFAULT_SUBAGENT)
    if rel.startswith("..") or not any(rel.startswith(prefix) for prefix in allowed):
        block(agent, tool, f"{agent} may only write in {', '.join(allowed)}; not {rel}")
sys.exit(0)
