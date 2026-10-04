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
    RUNS.mkdir(exist_ok=True)
    with AUDIT.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps({"ts": now(), **entry}, default=str) + "\n")
