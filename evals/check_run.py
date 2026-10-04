"""Score an agent report against the expected findings.
Usage:  python -m evals.check_run PSA-3 ba"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def fill(text: str, keys: dict) -> str:
    return re.sub(r"\{\{(S\d+)\}\}", lambda m: keys.get(m.group(1), m.group(1)), text)


def score(report: str, checks: list, keys: dict) -> list[tuple[str, bool]]:
    text = report.lower()
    results = []
    for check in checks:
        ok = all(any(fill(p, keys).lower() in text for p in group) for group in check["groups"])
        results.append((check["name"], ok))
    return results


def main():
    if len(sys.argv) != 3:
        sys.exit("Usage: python -m evals.check_run <TICKET-KEY> <ba|qa>")
    key, role = sys.argv[1].upper(), sys.argv[2].lower()
    keys = json.loads((ROOT / "seed_state.json").read_text())
    seed_id = next((sid for sid, k in keys.items() if k == key), None)
    expected = json.loads((ROOT / "evals" / "expected_findings.json").read_text())
    if seed_id not in expected or expected[seed_id]["role"] != role:
        sys.exit(f"No expected findings for {key} with role {role}. Demo tickets: "
                 + ", ".join(f"{keys[s]} ({v['role']})" for s, v in expected.items() if s in keys))
    report_path = ROOT / "runs" / "reports" / f"{key}-{role}.md"
    if not report_path.exists():
        sys.exit(f"Report not found: {report_path}")

    results = score(report_path.read_text(encoding="utf-8"), expected[seed_id]["checks"], keys)
    for name, ok in results:
        print(f"  [{'PASS' if ok else 'MISS'}] {name}")
    passed = sum(ok for _, ok in results)
    print(f"\n{key} ({role}): {passed}/{len(results)} expected findings present")


if __name__ == "__main__":
    main()
