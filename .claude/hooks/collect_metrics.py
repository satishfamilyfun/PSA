"""SubagentStop hook: measure the finished subagent run from its transcript and append one
record to runs/metrics/agent_runs.jsonl (tokens by type and model, API-equivalent cost,
duration, turns, tool calls and errors, plus story, task, mode and attempt)."""
import json
import re
from datetime import datetime
from pathlib import Path

from _hooklib import PROJECT, RUNS, active_ticket, now, read_event

PRICING = PROJECT / "metrics" / "pricing.json"
FIELDS = {"Mode": "mode", "Story": "story", "Task": "task", "Attempt": "attempt"}


def find_transcript(event: dict) -> Path | None:
    for key in ("agent_transcript_path", "subagent_transcript_path"):
        if event.get(key) and Path(event[key]).exists():
            return Path(event[key])
    main = Path(event.get("transcript_path") or "")
    folder = main.with_suffix("") / "subagents"
    if event.get("agent_id") and (folder / f"agent-{event['agent_id']}.jsonl").exists():
        return folder / f"agent-{event['agent_id']}.jsonl"
    candidates = sorted(folder.glob("agent-*.jsonl"), key=lambda p: p.stat().st_mtime) if folder.exists() else []
    return candidates[-1] if candidates else None


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    return " ".join(b.get("text", "") for b in content or [] if isinstance(b, dict))


def price_for(model: str, pricing: dict) -> dict:
    for family in ("haiku", "sonnet", "opus", "fable"):
        if family in model.lower() and family in pricing:
            return pricing[family]
    return pricing.get("sonnet", {"input": 0, "output": 0})


def summarize(lines: list[dict], pricing: dict) -> dict:
    seen, tool_ids, stamps = set(), set(), []
    by_model, header, errors = {}, {}, 0
    for item in lines:
        if item.get("timestamp"):
            stamps.append(item["timestamp"])
        msg = item.get("message") or {}
        if item.get("type") == "user":
            content = msg.get("content")
            if not header:
                for label, field in FIELDS.items():
                    match = re.search(rf"^{label}:\s*(\S+)", text_of(content), re.MULTILINE)
                    if match:
                        header[field] = match.group(1)
            if isinstance(content, list):
                errors += sum(1 for b in content if isinstance(b, dict)
                              and b.get("type") == "tool_result" and b.get("is_error"))
        if item.get("type") != "assistant":
            continue
        for block in msg.get("content") or []:
            if isinstance(block, dict) and block.get("type") == "tool_use":
                tool_ids.add(block.get("id"))
        msg_id = msg.get("id") or item.get("uuid")
        if msg_id in seen or not msg.get("usage"):
            continue  # transcripts repeat usage once per content block
        seen.add(msg_id)
        usage, model = msg["usage"], msg.get("model", "unknown")
        m = by_model.setdefault(model, {"input": 0, "output": 0, "cache_read": 0, "cache_write": 0})
        m["input"] += usage.get("input_tokens", 0)
        m["output"] += usage.get("output_tokens", 0)
        m["cache_read"] += usage.get("cache_read_input_tokens", 0)
        m["cache_write"] += usage.get("cache_creation_input_tokens", 0)

    cost = 0.0
    for model, m in by_model.items():
        p = price_for(model, pricing)
        cost += (m["input"] * p["input"] + m["output"] * p["output"]
                 + m["cache_read"] * p["input"] * pricing.get("cache_read_multiplier", 0.1)
                 + m["cache_write"] * p["input"] * pricing.get("cache_write_multiplier", 1.25)) / 1_000_000
    totals = {k: sum(m[k] for m in by_model.values()) for k in ("input", "output", "cache_read", "cache_write")}
    duration = 0.0
    if len(stamps) >= 2:
        parse = lambda s: datetime.fromisoformat(s.replace("Z", "+00:00"))
        duration = (parse(max(stamps)) - parse(min(stamps))).total_seconds()
    primary = max(by_model, key=lambda k: by_model[k]["output"]) if by_model else "unknown"
    return {**header, "model": primary, "models": by_model,
            "input_tokens": totals["input"], "output_tokens": totals["output"],
            "cache_read_tokens": totals["cache_read"], "cache_write_tokens": totals["cache_write"],
            "total_tokens": sum(totals.values()), "cost_usd_equiv": round(cost, 4),
            "duration_s": round(duration, 1), "turns": len(seen),
            "tool_calls": len(tool_ids), "tool_errors": errors}


def main():
    event = read_event()
    active = active_ticket()
    record = {"ts": now(), "agent": event.get("agent_type") or "unknown",
              "session_id": event.get("session_id"), "story": active.get("key"),
              "task": active.get("key"), "mode": active.get("role"), "attempt": "1"}
    transcript = find_transcript(event)
    if transcript:
        lines = []
        for raw in transcript.read_text(encoding="utf-8", errors="replace").splitlines():
            try:
                lines.append(json.loads(raw))
            except json.JSONDecodeError:
                continue
        pricing = json.loads(PRICING.read_text()) if PRICING.exists() else {}
        record.update({k: v for k, v in summarize(lines, pricing).items() if v not in (None, "")})
        record["transcript"] = str(transcript)
    else:
        record["note"] = "transcript not found"
    out = RUNS / "metrics"
    out.mkdir(parents=True, exist_ok=True)
    with (out / "agent_runs.jsonl").open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(record) + "\n")


if __name__ == "__main__":
    main()
