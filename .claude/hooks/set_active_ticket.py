"""UserPromptSubmit hook: when the user runs /ba-review KEY or /qa-design KEY,
record the ticket and role so the guard hook can restrict writes to that ticket."""
import json
import re

from _hooklib import ACTIVE, RUNS, audit, now, read_event

ROLES = {"ba-review": "ba", "qa-design": "qa"}

event = read_event()
match = re.search(r"/(ba-review|qa-design)\s+([A-Za-z]+-\d+)", event.get("prompt", ""))
if match:
    RUNS.mkdir(exist_ok=True)
    record = {"key": match.group(2).upper(), "role": ROLES[match.group(1)], "started_at": now()}
    ACTIVE.write_text(json.dumps(record, indent=2))
    audit({"event": "run_started", **record})
