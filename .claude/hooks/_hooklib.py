"""Shared helpers for the PSA hooks. Standard library only."""
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

PROJECT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
RUNS = PROJECT / "runs"
ACTIVE = RUNS / "active_ticket.json"
AUDIT = RUNS / "audit.jsonl"
SUBTASKS = RUNS / "guard" / "subtasks.json"
# Hook-owned state; no agent or session may change it with Write or Edit.
PROTECTED = ("runs/active_ticket.json", "runs/audit.jsonl", "runs/guard/")
PROJECT_KEY = "PSA"


def read_event() -> dict:
    try:
        return json.load(sys.stdin)
    except json.JSONDecodeError:
        return {}


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def active_ticket() -> dict:
    try:
        return json.loads(ACTIVE.read_text())
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def short(value, limit=300):
    text = value if isinstance(value, str) else json.dumps(value, default=str)
    return text if len(text) <= limit else text[:limit] + "...(truncated)"


def audit(entry: dict) -> None:
    """Append to the audit log. Never raises: a logging failure must not turn a block
    (exit code 2) into a crash (exit code 1), which Claude Code would treat as non-blocking."""
    try:
        RUNS.mkdir(parents=True, exist_ok=True)
        with AUDIT.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": now(), **entry}, default=str) + "\n")
    except OSError as err:
        print(f"audit log unavailable: {err}", file=sys.stderr)


def plan_subtasks(story_key: str) -> set[str]:
    """Sub-task keys recorded in the story's development plan (created by the senior developer)."""
    try:
        plan = json.loads((RUNS / "plans" / f"{story_key}-plan.json").read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()
    return {t["subtask_key"] for t in plan.get("tasks", []) if t.get("subtask_key")}


def created_subtasks(story_key: str) -> set[str]:
    """Sub-task keys the hooks saw created under the story. Agents cannot edit this file
    (guard_code_writes protects it), unlike the plan, so it bounds what a dev run may touch."""
    try:
        return set(json.loads(SUBTASKS.read_text(encoding="utf-8")).get(story_key, []))
    except (FileNotFoundError, json.JSONDecodeError):
        return set()


def record_subtask(story_key: str, subtask_key: str) -> None:
    try:
        data = json.loads(SUBTASKS.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        data = {}
    data[story_key] = sorted(set(data.get(story_key, [])) | {subtask_key})
    SUBTASKS.parent.mkdir(parents=True, exist_ok=True)
    SUBTASKS.write_text(json.dumps(data, indent=2), encoding="utf-8")
