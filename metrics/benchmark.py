"""Right-sizing benchmark: give the same junior-level coding task to each model tier
with Claude Code in headless mode, then score the result with hidden tests.

    python -m metrics.benchmark                  # haiku, sonnet, opus
    python -m metrics.benchmark --models haiku sonnet

Results are appended to runs/metrics/benchmark.jsonl and shown on the dashboard.
Uses your Claude Code login (Pro plan usage). A model your plan cannot use is recorded as unavailable.
"""
import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
BENCH = Path(__file__).resolve().parent / "benchmark"
OUT = ROOT / "runs" / "metrics" / "benchmark.jsonl"


def score_solution(solution: Path) -> tuple[int, int]:
    """Run the hidden tests against a solution file. Returns (passed, total)."""
    report = solution.with_suffix(".junit.xml")
    subprocess.run([sys.executable, "-m", "pytest", str(BENCH / "hidden_tests.py"), "-q", "--tb=no",
                    "-p", "no:cacheprovider", f"--junitxml={report}"],
                   env={**os.environ, "BENCH_SOLUTION": str(solution)}, capture_output=True, cwd=ROOT)
    if not report.exists():
        return 0, 0
    suite = ET.parse(report).getroot()
    suite = suite if suite.tag == "testsuite" else suite.find("testsuite")
    total = int(suite.get("tests", 0))
    if total == 0:  # collection failed (for example a syntax error in the solution)
        return 0, 25
    failed = int(suite.get("failures", 0)) + int(suite.get("errors", 0)) + int(suite.get("skipped", 0))
    return total - failed, total


def run_model(model: str, claude: str, timeout: int) -> dict:
    target = ROOT / "runs" / "benchmark" / model / "solution.py"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.unlink(missing_ok=True)
    prompt = (BENCH / "task.md").read_text(encoding="utf-8") + f"\nFile path: {target}\n"
    cmd = [claude, "-p", prompt, "--model", model, "--output-format", "json",
           "--allowedTools", "Write", "--disallowedTools", "Read,Glob,Grep,Bash,Edit,WebFetch,WebSearch",
           "--max-turns", "6"]
    record = {"ts": datetime.now(timezone.utc).isoformat(), "model": model, "task": "exif-helpers-v1"}
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, cwd=ROOT,
                              encoding="utf-8", errors="replace")
    except subprocess.TimeoutExpired:
        return {**record, "ok": False, "error": f"timed out after {timeout}s"}
    try:
        result = json.loads(proc.stdout.strip().splitlines()[-1])
    except (json.JSONDecodeError, IndexError):
        return {**record, "ok": False, "error": (proc.stderr or proc.stdout)[:300]}
    usage = result.get("usage") or {}
    record.update({
        "model_ids": sorted((result.get("modelUsage") or {}).keys()),
        "input_tokens": usage.get("input_tokens", 0), "output_tokens": usage.get("output_tokens", 0),
        "cache_read_tokens": usage.get("cache_read_input_tokens", 0),
        "cache_write_tokens": usage.get("cache_creation_input_tokens", 0),
        "cost_usd": round(result.get("total_cost_usd", 0) or 0, 4),
        "duration_s": round((result.get("duration_ms", 0) or 0) / 1000, 1),
        "turns": result.get("num_turns"),
    })
    if result.get("is_error") or not target.exists():
        text = str(result.get("result", ""))[:300]
        unavailable = re.search(r"not (currently )?(able|available)|usage credits|upgrade", text, re.I)
        return {**record, "ok": False, "error": ("model unavailable on this plan: " if unavailable else "") + text}
    passed, total = score_solution(target)
    return {**record, "ok": True, "passed": passed, "total": total,
            "score_pct": round(100 * passed / total) if total else 0}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--models", nargs="+", default=["haiku", "sonnet", "opus"])
    parser.add_argument("--timeout", type=int, default=300)
    args = parser.parse_args()
    claude = shutil.which("claude")
    if not claude:
        sys.exit("The 'claude' command was not found. Run this from a terminal where Claude Code works.")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    for model in args.models:
        print(f"Running {model}...", flush=True)
        record = run_model(model, claude, args.timeout)
        with OUT.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(record) + "\n")
        if record["ok"]:
            print(f"  {record['passed']}/{record['total']} tests passed, ${record['cost_usd']} API-equivalent, "
                  f"{record['duration_s']} s, {record['input_tokens'] + record['output_tokens']:,} tokens")
        else:
            print(f"  not scored: {record['error']}")
    print("\nRefresh the dashboard with: python -m metrics.report")


if __name__ == "__main__":
    main()
