"""Agent efficiency report.

    python -m metrics.report                 # all runs
    python -m metrics.report --story PSA-12  # one story (also prints a Markdown summary for Jira)

Reads runs/metrics/agent_runs.jsonl (collect_metrics hook), runs/metrics/benchmark.jsonl,
runs/audit.jsonl, runs/plans/*.json and runs/reports/*.md; writes runs/metrics/dashboard.html.
"""
import argparse
import json
from collections import defaultdict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
RUNS = ROOT / "runs"
WRITE_TOOLS = ("addOrEditJiraIssueComment", "editJiraIssue", "createJiraIssue", "transitionJiraIssue")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    rows = []
    for line in path.read_text(encoding="utf-8").splitlines():
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            pass
    return rows


def load_plans() -> dict[str, dict]:
    plans = {}
    for path in (RUNS / "plans").glob("*-plan.json"):
        try:
            plan = json.loads(path.read_text(encoding="utf-8"))
            plans[plan.get("story", path.stem.replace("-plan", ""))] = plan
        except json.JSONDecodeError:
            pass
    return plans


def eval_scores() -> list[dict]:
    """Score BA/QA reports against evals/expected_findings.json (quality metric)."""
    state_file = ROOT / "seed_state.json"
    if not state_file.exists():
        return []
    from evals.check_run import score
    keys = json.loads(state_file.read_text())
    expected = json.loads((ROOT / "evals" / "expected_findings.json").read_text())
    out = []
    for sid, spec in expected.items():
        if sid.startswith("_") or sid not in keys:
            continue
        report = RUNS / "reports" / f"{keys[sid]}-{spec['role']}.md"
        if report.exists():
            results = score(report.read_text(encoding="utf-8"), spec["checks"], keys)
            out.append({"ticket": keys[sid], "role": spec["role"],
                        "passed": sum(ok for _, ok in results), "total": len(results)})
    return out


def aggregate(runs: list[dict], plans: dict, audit: list[dict]) -> dict:
    by_agent = defaultdict(lambda: defaultdict(float))
    models = defaultdict(set)
    for r in runs:
        a = by_agent[r.get("agent", "unknown")]
        a["runs"] += 1
        for k in ("input_tokens", "output_tokens", "cache_read_tokens", "cache_write_tokens",
                  "total_tokens", "cost_usd_equiv", "duration_s", "turns", "tool_calls", "tool_errors"):
            a[k] += r.get(k, 0) or 0
        models[r.get("agent", "unknown")].add(r.get("model", "unknown"))

    tasks = [t for p in plans.values() for t in p.get("tasks", [])]
    approved = [t for t in tasks if t.get("status") == "approved"]
    first_pass = [t for t in approved if int(t.get("attempts", 1) or 1) == 1]
    rework_rounds = sum(max(int(t.get("attempts", 1) or 1) - 1, 0) for t in tasks)

    allowed = sum(1 for e in audit if e.get("event") == "write_allowed")
    executed = sum(1 for e in audit if e.get("event") == "tool_call"
                   and str(e.get("tool", "")).endswith(WRITE_TOOLS))
    blocked = [e for e in audit if e.get("event") == "blocked"]

    tot = lambda k: sum(r.get(k, 0) or 0 for r in runs)
    share = []
    for agent, a in by_agent.items():
        share.append({
            "agent": agent, "models": sorted(models[agent]), "runs": int(a["runs"]),
            "tokens": int(a["total_tokens"]), "cost": round(a["cost_usd_equiv"], 4),
            "token_pct": round(100 * a["total_tokens"] / tot("total_tokens"), 1) if tot("total_tokens") else 0,
            "cost_pct": round(100 * a["cost_usd_equiv"] / tot("cost_usd_equiv"), 1) if tot("cost_usd_equiv") else 0,
            "avg_tokens_per_run": round(a["total_tokens"] / a["runs"]) if a["runs"] else 0,
            "avg_cost_per_run": round(a["cost_usd_equiv"] / a["runs"], 4) if a["runs"] else 0,
        })
    share.sort(key=lambda row: (row["cost"], row["tokens"]), reverse=True)
    input_side = tot("input_tokens") + tot("cache_read_tokens") + tot("cache_write_tokens")
    return {
        "by_agent": {k: dict(v) for k, v in by_agent.items()},
        "share": share,
        "models": {k: sorted(v) for k, v in models.items()},
        "kpis": {
            "agent_runs": len(runs),
            "top_consumer": share[0]["agent"] if share else None,
            "top_consumer_cost_pct": share[0]["cost_pct"] if share else None,
            "total_tokens": tot("total_tokens"),
            "cost_usd_equiv": round(tot("cost_usd_equiv"), 2),
            "avg_duration_s": round(tot("duration_s") / len(runs), 1) if runs else 0,
            "cache_hit_ratio": round(tot("cache_read_tokens") / input_side, 2) if input_side else 0,
            "tool_error_rate": round(tot("tool_errors") / tot("tool_calls"), 3) if tot("tool_calls") else 0,
            "tasks": len(tasks),
            "tasks_approved": len(approved),
            "first_pass_approval": round(len(first_pass) / len(approved), 2) if approved else None,
            "rework_rounds": rework_rounds,
            "jira_writes_requested": allowed,
            "jira_writes_executed": executed,
            "jira_writes_declined": max(allowed - executed, 0),
            "guardrail_blocks": len(blocked),
            "tokens_per_approved_task": round(tot("total_tokens") / len(approved)) if approved else None,
            "cost_per_approved_task": round(tot("cost_usd_equiv") / len(approved), 3) if approved else None,
        },
        "blocked": [{"tool": b.get("tool"), "agent": b.get("agent", ""), "reason": b.get("reason")} for b in blocked],
    }


def markdown_summary(story: str, data: dict, plan: dict | None) -> str:
    k = data["kpis"]
    lines = [f"Agent metrics for {story}", "",
             f"Runs: {k['agent_runs']} | Tokens: {k['total_tokens']:,} | API-equivalent cost: ${k['cost_usd_equiv']} "
             f"| Avg run: {k['avg_duration_s']} s | Cache hit ratio: {k['cache_hit_ratio']}", ""]
    lines.append("Share of usage by agent (highest cost first):")
    lines.append("")
    lines.append("| Agent | Model | Runs | Tokens | % tokens | Cost (USD eq.) | % cost | Time (s) | Tool calls | Errors |")
    lines.append("|---|---|---|---|---|---|---|---|---|---|")
    for row in data["share"]:
        a = data["by_agent"][row["agent"]]
        lines.append(f"| {row['agent']} | {', '.join(row['models'])} | {row['runs']} | {row['tokens']:,} "
                     f"| {row['token_pct']}% | {row['cost']:.3f} | {row['cost_pct']}% | {a['duration_s']:.0f} "
                     f"| {int(a['tool_calls'])} | {int(a['tool_errors'])} |")
    if plan:
        lines += ["", "| Task | Sub-task | Agent | Status | Attempts |", "|---|---|---|---|---|"]
        for t in plan.get("tasks", []):
            lines.append(f"| {t.get('id')} {t.get('title')} | {t.get('subtask_key') or '-'} | {t.get('agent')} "
                         f"| {t.get('status')} | {t.get('attempts')} |")
    fp = k["first_pass_approval"]
    lines += ["", f"First-pass approval: {'n/a' if fp is None else f'{fp:.0%}'} | Rework rounds: {k['rework_rounds']} "
                  f"| Guardrail blocks: {k['guardrail_blocks']} | Jira writes declined by a person: {k['jira_writes_declined']}"]
    return "\n".join(lines)


def dashboard(data: dict, runs: list[dict], bench: list[dict], evals: list[dict], title: str) -> str:
    payload = json.dumps({"data": data, "runs": runs[-200:], "bench": bench, "evals": evals})
    return DASHBOARD_TEMPLATE.replace("__TITLE__", title).replace("__PAYLOAD__", payload.replace("</", "<\\/"))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--story", help="limit to one story key, for example PSA-12")
    args = parser.parse_args()

    runs = read_jsonl(RUNS / "metrics" / "agent_runs.jsonl")
    audit = read_jsonl(RUNS / "audit.jsonl")
    plans = load_plans()
    if args.story:
        story = args.story.upper()
        runs = [r for r in runs if r.get("story") == story]
        plans = {story: plans[story]} if story in plans else {}
    data = aggregate(runs, plans, audit)
    bench = read_jsonl(RUNS / "metrics" / "benchmark.jsonl")
    out = RUNS / "metrics" / "dashboard.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(dashboard(data, runs, bench, eval_scores(), args.story or "all stories"), encoding="utf-8")
    if args.story:
        print(markdown_summary(args.story.upper(), data, plans.get(args.story.upper())))
    else:
        print(json.dumps(data["kpis"], indent=2))
    print(f"\nDashboard: {out}")


DASHBOARD_TEMPLATE = r"""<!doctype html>
<html lang="en"><head><meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>PSA agent metrics - __TITLE__</title>
<script src="https://cdnjs.cloudflare.com/ajax/libs/Chart.js/4.4.1/chart.umd.min.js"></script>
<style>
  :root { --bg:#f6f5f2; --card:#fff; --ink:#1f2328; --muted:#6b6f76; --line:#e3e1dc;
          --a:#2f6f8f; --b:#d98a3d; --c:#6a9a5b; --d:#a05a8a; }
  * { box-sizing:border-box } body { margin:0; font-family:"Segoe UI",system-ui,sans-serif; background:var(--bg); color:var(--ink) }
  header { padding:24px 32px 8px } h1 { margin:0; font-size:22px } header p { margin:4px 0 0; color:var(--muted) }
  main { padding:16px 32px 40px; display:grid; gap:16px }
  .kpis { display:grid; grid-template-columns:repeat(auto-fit,minmax(160px,1fr)); gap:12px }
  .kpi, .card { background:var(--card); border:1px solid var(--line); border-radius:10px; padding:14px 16px }
  .kpi b { display:block; font-size:22px; margin-top:4px } .kpi span { color:var(--muted); font-size:13px }
  .grid { display:grid; grid-template-columns:repeat(auto-fit,minmax(420px,1fr)); gap:16px }
  h2 { font-size:15px; margin:0 0 10px } table { width:100%; border-collapse:collapse; font-size:13px }
  th, td { text-align:left; padding:6px 8px; border-bottom:1px solid var(--line) } th { color:var(--muted); font-weight:600 }
  .wrap { overflow-x:auto } .empty { color:var(--muted); font-size:13px }
  .bar { display:flex; align-items:center; gap:8px; min-width:160px }
  .bar i { display:block; height:10px; border-radius:5px; background:var(--a) } .bar.cost i { background:var(--b) }
</style></head><body>
<header><h1>PSA agent metrics</h1><p>Scope: __TITLE__. Cost is the API-equivalent estimate from metrics/pricing.json, not your Pro bill.</p></header>
<main>
  <section class="kpis" id="kpis"></section>
  <section class="card"><h2>Share of usage by agent (highest cost first)</h2><div class="wrap"><table id="share"></table></div></section>
  <section class="grid">
    <div class="card"><h2>Tokens by agent</h2><canvas id="tokens"></canvas></div>
    <div class="card"><h2>API-equivalent cost and time by agent</h2><canvas id="cost"></canvas></div>
    <div class="card"><h2>Model benchmark: quality vs cost (same task)</h2><canvas id="bench"></canvas><p class="empty" id="benchEmpty"></p></div>
    <div class="card"><h2>Quality: eval scores of BA and QA reports</h2><div class="wrap"><table id="evals"></table></div></div>
  </section>
  <section class="card"><h2>Agent runs</h2><div class="wrap"><table id="runs"></table></div></section>
  <section class="card"><h2>Guardrail blocks</h2><div class="wrap"><table id="blocked"></table></div></section>
</main>
<script>
const P = __PAYLOAD__;
const k = P.data.kpis, fmt = n => n == null ? "n/a" : Number(n).toLocaleString();
const pct = n => n == null ? "n/a" : Math.round(n * 100) + "%";
const kpis = [["Top consumer", k.top_consumer ? `${k.top_consumer} (${k.top_consumer_cost_pct}% of cost)` : "n/a"],
  ["Agent runs", fmt(k.agent_runs)], ["Total tokens", fmt(k.total_tokens)],
  ["API-equiv. cost", "$" + k.cost_usd_equiv], ["Avg run time", k.avg_duration_s + " s"],
  ["Cache hit ratio", pct(k.cache_hit_ratio)], ["Tool error rate", pct(k.tool_error_rate)],
  ["First-pass approval", pct(k.first_pass_approval)], ["Rework rounds", fmt(k.rework_rounds)],
  ["Cost per approved task", k.cost_per_approved_task == null ? "n/a" : "$" + k.cost_per_approved_task],
  ["Guardrail blocks", fmt(k.guardrail_blocks)], ["Jira writes declined", fmt(k.jira_writes_declined)]];
document.getElementById("kpis").innerHTML = kpis.map(([l, v]) => `<div class="kpi"><span>${l}</span><b>${v}</b></div>`).join("");

const agents = Object.keys(P.data.by_agent).sort(), A = a => P.data.by_agent[a];
const css = v => getComputedStyle(document.documentElement).getPropertyValue(v).trim();
new Chart(document.getElementById("tokens"), { type: "bar", data: { labels: agents, datasets: [
  ["Input", "input_tokens", "--a"], ["Output", "output_tokens", "--b"],
  ["Cache read", "cache_read_tokens", "--c"], ["Cache write", "cache_write_tokens", "--d"]
].map(([label, key, c]) => ({ label, data: agents.map(a => A(a)[key] || 0), backgroundColor: css(c) })) },
  options: { scales: { x: { stacked: true }, y: { stacked: true, title: { display: true, text: "tokens" } } } } });
new Chart(document.getElementById("cost"), { type: "bar", data: { labels: agents, datasets: [
  { label: "Cost (USD eq.)", data: agents.map(a => +(A(a).cost_usd_equiv || 0).toFixed(3)), backgroundColor: css("--a"), yAxisID: "y" },
  { label: "Time (s)", data: agents.map(a => Math.round(A(a).duration_s || 0)), backgroundColor: css("--b"), yAxisID: "y1" }] },
  options: { scales: { y: { position: "left", title: { display: true, text: "USD" } },
                       y1: { position: "right", grid: { drawOnChartArea: false }, title: { display: true, text: "seconds" } } } } });

const ok = P.bench.filter(b => b.ok);
if (ok.length) {
  new Chart(document.getElementById("bench"), { type: "bar", data: { labels: ok.map(b => b.model), datasets: [
    { label: "Tests passed (%)", data: ok.map(b => b.score_pct), backgroundColor: css("--c"), yAxisID: "y" },
    { label: "Cost (USD eq.)", data: ok.map(b => b.cost_usd), backgroundColor: css("--a"), yAxisID: "y1" }] },
    options: { scales: { y: { max: 100, title: { display: true, text: "% of hidden tests passed" } },
                         y1: { position: "right", grid: { drawOnChartArea: false }, title: { display: true, text: "USD" } } } } });
} else document.getElementById("benchEmpty").textContent = "No benchmark yet: run python -m metrics.benchmark";

const table = (id, head, rows) => document.getElementById(id).innerHTML = rows.length
  ? `<tr>${head.map(h => `<th>${h}</th>`).join("")}</tr>` + rows.map(r => `<tr>${r.map(c => `<td>${c ?? ""}</td>`).join("")}</tr>`).join("")
  : `<tr><td class="empty">No data yet</td></tr>`;
const bar = (pct, cls) => `<span class="bar ${cls}"><i style="width:${Math.max(pct, 1)}%"></i>${pct}%</span>`;
table("share", ["Agent", "Model", "Runs", "Tokens", "Share of tokens", "Cost (USD eq.)", "Share of cost", "Avg tokens per run"],
  P.data.share.map(s => [s.agent, s.models.join(", "), s.runs, fmt(s.tokens), bar(s.token_pct, ""), "$" + s.cost,
    bar(s.cost_pct, "cost"), fmt(s.avg_tokens_per_run)]));
table("evals", ["Ticket", "Role", "Findings found", "Score"], P.evals.map(e => [e.ticket, e.role, `${e.passed}/${e.total}`, pct(e.passed / e.total)]));
table("runs", ["When", "Agent", "Model", "Story", "Task", "Mode", "Try", "Tokens", "Cost", "Time (s)", "Tools", "Errors"],
  P.runs.slice().reverse().map(r => [(r.ts || "").slice(0, 16).replace("T", " "), r.agent, r.model, r.story, r.task, r.mode, r.attempt,
    fmt(r.total_tokens), r.cost_usd_equiv, r.duration_s, r.tool_calls, r.tool_errors]));
table("blocked", ["Tool", "Agent", "Reason"], P.data.blocked.map(b => [b.tool, b.agent, b.reason]));
</script></body></html>
"""

if __name__ == "__main__":
    main()
