"""Offline tests for the developer-team guardrails, metrics collection, report and benchmark scoring."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / ".claude" / "hooks"


def run_hook(name, event, project, cwd=None):
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project)}
    return subprocess.run([sys.executable, str(HOOKS / name)], input=json.dumps(event),
                          capture_output=True, text=True, env=env, cwd=cwd)


def write_event(agent, path):
    return {"tool_name": "Write", "agent_type": agent, "tool_input": {"file_path": path, "content": "x"}}


def bash_event(command, agent=None):
    event = {"tool_name": "Bash", "tool_input": {"command": command}}
    return {**event, "agent_type": agent} if agent else event


# ---------- guard_code_writes: folder ownership ----------

@pytest.mark.parametrize("agent,rel,allowed", [
    ("database-developer", "app/core/db/migrations/002_exif.sql", True),
    ("database-developer", "app/tests/test_db_exif.py", True),
    ("database-developer", "app/core/metadata/exif.py", False),
    ("junior-developer", "app/core/utils/dates.py", True),
    ("junior-developer", "app/tests/test_dates.py", True),
    ("junior-developer", "app/core/db/database.py", False),
    ("ui-developer", "app/ui/src/components/PhotoMetadataPanel.tsx", True),
    ("ui-developer", "app/ui/package.json", False),
    ("senior-developer", "app/core/metadata/exif.py", True),
    ("senior-developer", "runs/plans/PSA-12-plan.json", True),
    ("senior-developer", ".claude/settings.json", False),
    ("ba-agent", "app/core/utils/x.py", False),
    ("general-purpose", "app/core/utils/x.py", False),
])
def test_ownership_posix(tmp_path, agent, rel, allowed):
    result = run_hook("guard_code_writes.py", write_event(agent, str(tmp_path / rel)), tmp_path)
    assert (result.returncode == 0) == allowed, result.stderr


def test_ownership_windows_paths(tmp_path):
    # Fake drive Q: so the audit log can never land in a real project folder.
    project = r"Q:\psa-test\photoapp"
    ok = run_hook("guard_code_writes.py",
                  write_event("database-developer", r"Q:\PSA-Test\PhotoApp\app\core\db\migrations\002.sql"),
                  project, cwd=tmp_path)
    bad = run_hook("guard_code_writes.py",
                   write_event("junior-developer", r"Q:\psa-test\photoapp\app\core\db\database.py"),
                   project, cwd=tmp_path)
    assert ok.returncode == 0 and bad.returncode == 2


def test_main_session_not_restricted_by_ownership(tmp_path):
    event = {"tool_name": "Write", "tool_input": {"file_path": str(tmp_path / "README.md")}}
    assert run_hook("guard_code_writes.py", event, tmp_path).returncode == 0


# ---------- guard_code_writes: commands ----------

@pytest.mark.parametrize("command,agent,allowed", [
    ("git push -u origin feature/PSA-12-exif-metadata", None, True),
    ("git push origin main", None, False),
    ("git push --force origin feature/x", None, False),
    ("git reset --hard HEAD~1", None, False),
    ("gh pr merge 3", None, False),
    ("rm -rf app", None, False),
    ("Remove-Item -Recurse app", None, False),
    ("python -m pytest app -q 2>&1", "junior-developer", True),
    ("npm --prefix app/ui test", "ui-developer", True),
    ("git diff", "senior-developer", True),
    ("git commit -m 'x'", "junior-developer", False),
    ("npm install lodash", "ui-developer", False),
    ("echo hi > app/core/utils/x.py", "junior-developer", False),
    ("git commit -m 'feat: exif (PSA-12)'", None, True),
])
def test_commands(tmp_path, command, agent, allowed):
    result = run_hook("guard_code_writes.py", bash_event(command, agent), tmp_path)
    assert (result.returncode == 0) == allowed, result.stderr


# ---------- guard_jira_writes: dev role ----------

@pytest.fixture
def dev_project(tmp_path):
    run_hook("set_active_ticket.py", {"prompt": "/dev-implement PSA-12 including a metadata panel"}, tmp_path)
    plans = tmp_path / "runs" / "plans"
    plans.mkdir(parents=True)
    (plans / "PSA-12-plan.json").write_text(json.dumps({"story": "PSA-12", "tasks": [
        {"id": "T1", "subtask_key": "PSA-30"}, {"id": "T2", "subtask_key": "PSA-31"}]}))
    return tmp_path


def jira(tool, tool_input):
    return {"tool_name": f"mcp__atlassian__{tool}", "tool_input": tool_input}


def test_dev_can_create_subtask_under_story(dev_project):
    event = jira("createJiraIssue", {"projectKey": "PSA", "issueTypeName": "Subtask",
                                     "parent": "PSA-12", "summary": "[database-developer] Add EXIF columns"})
    assert run_hook("guard_jira_writes.py", event, dev_project).returncode == 0


@pytest.mark.parametrize("tool_input", [
    {"projectKey": "PSA", "issueTypeName": "Story", "summary": "new story"},
    {"projectKey": "PSA", "issueTypeName": "Subtask", "parent": "PSA-7", "summary": "x"},
])
def test_dev_cannot_create_other_issues(dev_project, tool_input):
    assert run_hook("guard_jira_writes.py", jira("createJiraIssue", tool_input), dev_project).returncode == 2


def test_ba_cannot_create_subtask(tmp_path):
    run_hook("set_active_ticket.py", {"prompt": "/ba-review PSA-12"}, tmp_path)
    event = jira("createJiraIssue", {"issueTypeName": "Subtask", "parent": "PSA-12"})
    assert run_hook("guard_jira_writes.py", event, tmp_path).returncode == 2


def test_dev_transitions(dev_project):
    sub = jira("transitionJiraIssue", {"issueIdOrKey": "PSA-30", "transition": {"id": "31"}})
    story = jira("transitionJiraIssue", {"issueIdOrKey": "PSA-12", "transition": {"id": "31"}})
    other = jira("transitionJiraIssue", {"issueIdOrKey": "PSA-40", "transition": {"id": "31"}})
    assert run_hook("guard_jira_writes.py", sub, dev_project).returncode == 0
    assert run_hook("guard_jira_writes.py", story, dev_project).returncode == 2
    assert run_hook("guard_jira_writes.py", other, dev_project).returncode == 2


def test_dev_comment_on_story_and_subtask(dev_project):
    for key in ("PSA-12", "PSA-31"):
        event = jira("addOrEditJiraIssueComment", {"issueIdOrKey": key, "commentBody": "metrics"})
        assert run_hook("guard_jira_writes.py", event, dev_project).returncode == 0


# ---------- collect_metrics ----------

def transcript_lines():
    header = "Mode: BUILD\nStory: PSA-12\nTask: PSA-30\nAttempt: 2\n\nAdd EXIF columns."
    usage = {"input_tokens": 100, "output_tokens": 50, "cache_read_input_tokens": 1000,
             "cache_creation_input_tokens": 200}
    return [
        {"type": "user", "timestamp": "2026-10-05T10:00:00Z", "message": {"role": "user", "content": header}},
        # one API message split over two lines (text + tool_use) with repeated usage: must count once
        {"type": "assistant", "timestamp": "2026-10-05T10:00:05Z",
         "message": {"id": "m1", "model": "claude-sonnet-5", "usage": usage, "content": [{"type": "text", "text": "ok"}]}},
        {"type": "assistant", "timestamp": "2026-10-05T10:00:06Z",
         "message": {"id": "m1", "model": "claude-sonnet-5", "usage": usage,
                     "content": [{"type": "tool_use", "id": "t1", "name": "Write", "input": {}}]}},
        {"type": "user", "timestamp": "2026-10-05T10:00:07Z",
         "message": {"content": [{"type": "tool_result", "tool_use_id": "t1", "is_error": True, "content": "denied"}]}},
        {"type": "assistant", "timestamp": "2026-10-05T10:01:00Z",
         "message": {"id": "m2", "model": "claude-sonnet-5", "usage": {"input_tokens": 10, "output_tokens": 20},
                     "content": [{"type": "text", "text": "done"}]}},
    ]


def test_collect_metrics_hook(tmp_path):
    (tmp_path / "metrics").mkdir()
    (tmp_path / "metrics" / "pricing.json").write_text((ROOT / "metrics" / "pricing.json").read_text())
    transcript = tmp_path / "agent-abc.jsonl"
    transcript.write_text("\n".join(json.dumps(line) for line in transcript_lines()))
    run_hook("set_active_ticket.py", {"prompt": "/dev-implement PSA-12"}, tmp_path)
    result = run_hook("collect_metrics.py", {"agent_type": "database-developer",
                                             "agent_transcript_path": str(transcript)}, tmp_path)
    assert result.returncode == 0, result.stderr
    record = json.loads((tmp_path / "runs" / "metrics" / "agent_runs.jsonl").read_text().splitlines()[-1])
    assert (record["task"], record["story"], record["mode"], record["attempt"]) == ("PSA-30", "PSA-12", "BUILD", "2")
    assert record["input_tokens"] == 110 and record["output_tokens"] == 70      # m1 counted once
    assert record["cache_read_tokens"] == 1000 and record["turns"] == 2
    assert record["tool_calls"] == 1 and record["tool_errors"] == 1
    assert record["duration_s"] == 60.0 and record["model"] == "claude-sonnet-5"
    expected = (110 * 3 + 70 * 15 + 1000 * 3 * 0.1 + 200 * 3 * 1.25) / 1_000_000
    assert record["cost_usd_equiv"] == pytest.approx(expected, abs=1e-4)


def test_collect_metrics_finds_subagent_folder(tmp_path):
    main = tmp_path / "session-1.jsonl"
    main.write_text("")
    folder = tmp_path / "session-1" / "subagents"
    folder.mkdir(parents=True)
    (folder / "agent-xyz.jsonl").write_text("\n".join(json.dumps(line) for line in transcript_lines()))
    result = run_hook("collect_metrics.py", {"agent_type": "junior-developer", "transcript_path": str(main)}, tmp_path)
    assert result.returncode == 0
    record = json.loads((tmp_path / "runs" / "metrics" / "agent_runs.jsonl").read_text())
    assert record["agent"] == "junior-developer" and record["output_tokens"] == 70


# ---------- report ----------

def test_report_aggregate_and_dashboard(tmp_path, monkeypatch):
    from metrics import report
    runs = [{"agent": "database-developer", "model": "claude-sonnet-5", "story": "PSA-12", "total_tokens": 1000,
             "input_tokens": 100, "output_tokens": 100, "cache_read_tokens": 800, "cache_write_tokens": 0,
             "cost_usd_equiv": 0.01, "duration_s": 30, "tool_calls": 4, "tool_errors": 1},
            {"agent": "junior-developer", "model": "claude-haiku-4-5", "story": "PSA-12", "total_tokens": 500,
             "input_tokens": 400, "output_tokens": 100, "cost_usd_equiv": 0.001, "duration_s": 10, "tool_calls": 2}]
    plans = {"PSA-12": {"story": "PSA-12", "tasks": [
        {"id": "T1", "agent": "database-developer", "status": "approved", "attempts": 1, "subtask_key": "PSA-30"},
        {"id": "T2", "agent": "junior-developer", "status": "approved", "attempts": 2, "subtask_key": "PSA-31"}]}}
    audit = [{"event": "write_allowed"}, {"event": "write_allowed"},
             {"event": "tool_call", "tool": "mcp__atlassian__addOrEditJiraIssueComment"},
             {"event": "blocked", "tool": "Bash", "agent": "junior-developer", "reason": "git write commands"}]
    data = report.aggregate(runs, plans, audit)
    k = data["kpis"]
    assert k["first_pass_approval"] == 0.5 and k["rework_rounds"] == 1
    assert k["jira_writes_declined"] == 1 and k["guardrail_blocks"] == 1
    assert k["cache_hit_ratio"] == pytest.approx(800 / 1300, abs=0.01)
    summary = report.markdown_summary("PSA-12", data, plans["PSA-12"])
    assert "First-pass approval: 50%" in summary and "| PSA-31 |" in summary
    html = report.dashboard(data, runs, [{"ok": True, "model": "haiku", "score_pct": 90, "cost_usd": 0.01}], [], "PSA-12")
    assert "chart.umd.min.js" in html and '"first_pass_approval": 0.5' in html


# ---------- benchmark scoring ----------

def test_benchmark_scores_reference_and_broken(tmp_path):
    from metrics.benchmark import score_solution
    good = tmp_path / "good.py"
    good.write_text((ROOT / "metrics" / "benchmark" / "reference_solution.py").read_text())
    broken = tmp_path / "broken.py"
    broken.write_text("def dms_to_decimal(:\n")
    passed, total = score_solution(good)
    assert passed == total == 22
    assert score_solution(broken)[0] == 0


# ---------- orchestrator (main session) metrics ----------

def assistant(msg_id, out, sidechain=False, ts="2026-10-05T11:00:00Z"):
    line = {"type": "assistant", "timestamp": ts,
            "message": {"id": msg_id, "model": "claude-sonnet-5", "content": [{"type": "text", "text": "x"}],
                        "usage": {"input_tokens": 10, "output_tokens": out}}}
    return {**line, "isSidechain": True} if sidechain else line


def test_orchestrator_counts_only_new_lines(tmp_path):
    transcript = tmp_path / "session-9.jsonl"
    run_hook("set_active_ticket.py", {"prompt": "/dev-implement PSA-12"}, tmp_path)
    event = {"session_id": "session-9", "transcript_path": str(transcript)}

    # Turn 1: one orchestrator message plus one sidechain (subagent) message that must be skipped
    transcript.write_text("\n".join(json.dumps(x) for x in [assistant("o1", 100), assistant("s1", 999, True)]))
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(tmp_path)}
    call = lambda: subprocess.run([sys.executable, str(HOOKS / "collect_metrics.py"), "--orchestrator"],
                                  input=json.dumps(event), capture_output=True, text=True, env=env)
    assert call().returncode == 0
    # Turn 2: transcript grows by one message; only the new one may be counted
    with transcript.open("a") as fh:
        fh.write("\n" + json.dumps(assistant("o2", 40)))
    assert call().returncode == 0
    # Turn 3: nothing new, so no record
    assert call().returncode == 0

    rows = [json.loads(x) for x in (tmp_path / "runs" / "metrics" / "agent_runs.jsonl").read_text().splitlines()]
    assert [r["output_tokens"] for r in rows] == [100, 40]
    assert all(r["agent"] == "orchestrator" and r["story"] == "PSA-12" and r["mode"] == "dev" for r in rows)


def test_share_ranking_and_top_consumer():
    from metrics import report
    runs = [{"agent": "orchestrator", "model": "claude-sonnet-5", "total_tokens": 3000, "cost_usd_equiv": 0.03},
            {"agent": "senior-developer", "model": "claude-opus-5", "total_tokens": 2000, "cost_usd_equiv": 0.06},
            {"agent": "junior-developer", "model": "claude-haiku-4-5", "total_tokens": 5000, "cost_usd_equiv": 0.01}]
    data = report.aggregate(runs, {}, [])
    assert [r["agent"] for r in data["share"]] == ["senior-developer", "orchestrator", "junior-developer"]
    assert data["share"][0]["cost_pct"] == 60.0 and data["share"][2]["token_pct"] == 50.0
    assert data["kpis"]["top_consumer"] == "senior-developer"
    summary = report.markdown_summary("PSA-12", data, None)
    assert "| senior-developer | claude-opus-5 | 1 | 2,000 | 20.0% | 0.060 | 60.0% |" in summary
