"""Offline tests for the hooks, the psa MCP tool and the evaluator. No network needed."""
import json
import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
HOOKS = ROOT / ".claude" / "hooks"


def run_hook(name: str, event: dict, project: Path) -> subprocess.CompletedProcess:
    env = {**os.environ, "CLAUDE_PROJECT_DIR": str(project)}
    return subprocess.run([sys.executable, str(HOOKS / name)], input=json.dumps(event),
                          capture_output=True, text=True, env=env)


@pytest.fixture
def project(tmp_path):
    run_hook("set_active_ticket.py", {"prompt": "/ba-review PSA-3"}, tmp_path)
    return tmp_path


# ---------- hooks ----------

def test_prompt_hook_records_active_ticket(project):
    active = json.loads((project / "runs" / "active_ticket.json").read_text())
    assert active["key"] == "PSA-3" and active["role"] == "ba"


@pytest.mark.parametrize("tool", ["executeDestructive", "executeWrite", "createJiraIssue",
                                  "transitionJiraIssue", "updateConfluenceContent"])
def test_guard_blocks_dangerous_tools(project, tool):
    result = run_hook("guard_jira_writes.py", {"tool_name": f"mcp__atlassian__{tool}", "tool_input": {}}, project)
    assert result.returncode == 2 and "Blocked" in result.stderr


def test_guard_allows_comment_on_active_ticket(project):
    event = {"tool_name": "mcp__atlassian__addOrEditJiraIssueComment",
             "tool_input": {"cloudId": "abc", "issueIdOrKey": "PSA-3", "commentBody": "BA review..."}}
    assert run_hook("guard_jira_writes.py", event, project).returncode == 0


def test_guard_blocks_other_ticket(project):
    event = {"tool_name": "mcp__atlassian__addOrEditJiraIssueComment",
             "tool_input": {"issueIdOrKey": "PSA-7", "commentBody": "x"}}
    result = run_hook("guard_jira_writes.py", event, project)
    assert result.returncode == 2 and "PSA-3" in result.stderr


def test_guard_ignores_keys_cited_in_body(project):
    event = {"tool_name": "mcp__atlassian__addOrEditJiraIssueComment",
             "tool_input": {"issueIdOrKey": "PSA-3", "commentBody": "Blocked by PSA-9; see NFR-6 and FR-1.6"}}
    assert run_hook("guard_jira_writes.py", event, project).returncode == 0


def test_guard_blocks_other_project(project):
    event = {"tool_name": "mcp__atlassian__addOrEditJiraIssueComment",
             "tool_input": {"issueIdOrKey": "ABC-3", "commentBody": "x"}}
    assert run_hook("guard_jira_writes.py", event, project).returncode == 2


def test_guard_blocks_editing_existing_comment(project):
    event = {"tool_name": "mcp__atlassian__addOrEditJiraIssueComment",
             "tool_input": {"issueIdOrKey": "PSA-3", "commentId": "10001", "commentBody": "x"}}
    assert run_hook("guard_jira_writes.py", event, project).returncode == 2


def test_guard_limits_edit_fields(project):
    ok = {"tool_name": "mcp__atlassian__editJiraIssue",
          "tool_input": {"issueIdOrKey": "PSA-3", "fields": {"description": "...", "labels": ["x"]}}}
    bad = {"tool_name": "mcp__atlassian__editJiraIssue",
           "tool_input": {"issueIdOrKey": "PSA-3", "fields": {"summary": "new title"}}}
    assert run_hook("guard_jira_writes.py", ok, project).returncode == 0
    assert run_hook("guard_jira_writes.py", bad, project).returncode == 2


def test_guard_qa_role_labels_only(tmp_path):
    run_hook("set_active_ticket.py", {"prompt": "/qa-design PSA-5"}, tmp_path)
    event = {"tool_name": "mcp__atlassian__editJiraIssue",
             "tool_input": {"issueIdOrKey": "PSA-5", "fields": {"description": "..."}}}
    assert run_hook("guard_jira_writes.py", event, tmp_path).returncode == 2


def test_guard_ignores_read_tools(project):
    event = {"tool_name": "mcp__atlassian__getJiraIssue", "tool_input": {"issueIdOrKey": "PSA-99"}}
    assert run_hook("guard_jira_writes.py", event, project).returncode == 0


def test_audit_and_trace(project):
    run_hook("audit_log.py", {"tool_name": "mcp__psa__get_ticket_bundle",
                              "tool_input": {"issue_key": "PSA-3"}, "tool_response": "ok"}, project)
    run_hook("guard_jira_writes.py", {"tool_name": "mcp__atlassian__executeWrite", "tool_input": {}}, project)
    run_hook("run_trace.py", {"agent_type": "ba-agent"}, project)
    trace = next((project / "runs" / "traces").glob("*-ba-agent-PSA-3.md")).read_text()
    assert "mcp__psa__get_ticket_bundle: 1" in trace
    assert "executeWrite" in trace  # blocked action recorded


# ---------- psa MCP tool ----------

class FakeResponse:
    content = b"File: IMG.HEIC\nGPSLatitude: (none)"

    def raise_for_status(self):
        pass


class FakeAPI:
    class session:
        @staticmethod
        def get(url, timeout=None):
            return FakeResponse()

    def get(self, path):
        adf = lambda t: {"type": "doc", "content": [{"type": "paragraph", "content": [{"type": "text", "text": t}]}]}
        comment = lambda t: {"author": {"displayName": "Satish"}, "created": "2026-10-04T10:00", "body": adf(t)}
        if path.startswith("/rest/api/3/issue/PSA-6?"):
            return {"fields": {
                "summary": "Face labeling UI", "issuetype": {"name": "Story"}, "status": {"name": "To Do"},
                "labels": ["phase-1"], "parent": {"key": "PSA-3", "fields": {"summary": "People recognition"}},
                "description": adf("Build a screen where users can name people."),
                "comment": {"comments": [comment("kids will use this")]},
                "attachment": [{"filename": "notes.txt", "mimeType": "text/plain", "size": 30, "content": "u"},
                               {"filename": "mockup.png", "mimeType": "image/png", "size": 9, "content": "u"}],
                "issuelinks": [
                    {"type": {"inward": "is blocked by", "outward": "blocks"},
                     "inwardIssue": {"key": "PSA-5",
                                     "fields": {"summary": "Face clustering", "status": {"name": "To Do"}}}},
                    {"type": {"inward": "is blocked by", "outward": "blocks"},
                     "outwardIssue": {"key": "PSA-7", "fields": {"summary": "Search", "status": {"name": "To Do"}}}}]}}
        if path.startswith("/rest/api/3/issue/PSA-5?"):
            return {"fields": {"description": adf("Cluster faces."),
                               "comment": {"comments": [comment("5 or 10 sample faces?")]}}}
        raise AssertionError(path)


def test_ticket_bundle(monkeypatch, tmp_path):
    sys.path.insert(0, str(ROOT / "tools"))
    import psa_tools_mcp
    monkeypatch.setattr(psa_tools_mcp, "RUNS", tmp_path / "runs")
    bundle = psa_tools_mcp.build_bundle(FakeAPI(), "psa-6")
    assert "PSA-6 is blocked by PSA-5: Face clustering [To Do]" in bundle
    assert "5 or 10 sample faces?" in bundle            # blocker's open question surfaced
    assert "PSA-6 blocks PSA-7" in bundle and "Cluster faces." in bundle
    assert "GPSLatitude: (none)" in bundle              # text attachment inlined
    assert "Open it with the Read tool" in bundle       # image saved for viewing
    assert (tmp_path / "runs" / "attachments" / "PSA-6" / "mockup.png").exists()
    assert json.loads((tmp_path / "runs" / "active_ticket.json").read_text())["key"] == "PSA-6"


def test_mcp_server_registers_tool():
    sys.path.insert(0, str(ROOT / "tools"))
    import asyncio

    import psa_tools_mcp
    tools = asyncio.run(psa_tools_mcp.server.list_tools())
    assert [t.name for t in tools] == ["get_ticket_bundle"]


# ---------- evaluator ----------

def test_eval_scoring():
    from evals.check_run import score
    checks = json.loads((ROOT / "evals" / "expected_findings.json").read_text())["S6"]["checks"]
    keys = {"S5": "PSA-9"}
    good = ("Blocked by PSA-9 which is still To Do. Open question 5 or 10 faces, but the mockup shows 6 faces. "
            "Limit of 15 tracked people; others Unknown. Kids will use it. Label: needs-clarification.")
    assert all(ok for _, ok in score(good, checks, keys))
    assert not all(ok for _, ok in score("Looks fine.", checks, keys))
