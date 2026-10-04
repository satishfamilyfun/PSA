"""Offline tests: run with `pytest`. No network or Atlassian account needed."""
import json
import re

import pytest

from common.atlassian import adf_to_text, normalize, text_to_adf
from seed import reset_demo, seed_confluence, seed_jira
from seed.seed_data import BLOCKS, DEMO_TARGETS, EPICS, STORIES


class FakeAtlassian:
    """Records calls and returns minimal, realistic responses."""

    def __init__(self):
        self.calls, self.counter, self.links = [], 0, {}
        self.comments = {}

    def get(self, path, **kw):
        self.calls.append(("GET", path))
        if path.startswith("/rest/api/3/project/"):
            return {"issueTypes": [{"name": n, "subtask": False} for n in ("Epic", "Story", "Task")]}
        if "fields=issuelinks" in path:
            return {"fields": {"issuelinks": self.links.get(path.split("/")[5].split("?")[0], [])}}
        if path.endswith("/comment?maxResults=100"):
            return {"comments": self.comments.get(path.split("/")[5], [])}
        if path.startswith("/wiki/api/v2/spaces"):
            return {"results": [{"id": "123"}]}
        if path == "/wiki/api/v2/pages":
            return {"results": []}
        raise AssertionError(f"unexpected GET {path}")

    def post(self, path, json=None, **kw):
        self.calls.append(("POST", path, json))
        if path == "/rest/api/3/issue":
            self.counter += 1
            return {"key": f"PSA-{self.counter}"}
        if path == "/rest/api/3/issueLink" and json["type"]["name"] == "Blocks":
            blocked, blocker = json["outwardIssue"]["key"], json["inwardIssue"]["key"]
            self.links.setdefault(blocked, []).append(
                {"id": "1", "type": {"name": "Blocks"}, "inwardIssue": {"key": blocker}})
        return {}

    def put(self, path, json=None, **kw):
        self.calls.append(("PUT", path, json))

    def delete(self, path, **kw):
        self.calls.append(("DELETE", path))


@pytest.fixture
def fake(monkeypatch, tmp_path):
    api = FakeAtlassian()
    for module in (seed_jira, reset_demo, seed_confluence):
        monkeypatch.setattr(module, "Atlassian", lambda: api)
        monkeypatch.setattr(module, "STATE_FILE", tmp_path / "seed_state.json", raising=False)
    monkeypatch.setattr(seed_jira, "env", lambda name: "PSA")
    monkeypatch.setattr(seed_confluence, "env", lambda name: "PSA")
    monkeypatch.setattr("sys.argv", ["seed"])
    return api


def test_adf_round_trip():
    adf = text_to_adf("Intro line.\n\n## Acceptance criteria\n- Given A, then B.\n- Given C, then D.")
    assert [n["type"] for n in adf["content"]] == ["paragraph", "heading", "bulletList"]
    assert "Given C, then D." in adf_to_text(adf)


def test_seed_creates_everything(fake, tmp_path):
    seed_jira.main()
    created = [c for c in fake.calls if c[:2] == ("POST", "/rest/api/3/issue")]
    assert len(created) == len(EPICS) + len(STORIES)
    state = json.loads((tmp_path / "seed_state.json").read_text())
    assert all(sid in state for sid in DEMO_TARGETS.values())
    attachments = [c for c in fake.calls if c[1].endswith("/attachments")]
    assert len(attachments) == sum(len(s.get("attachments", [])) for s in STORIES)
    stories_with_parent = [c for c in created if "parent" in c[2]["fields"]]
    assert len(stories_with_parent) == len(STORIES)
    blocks = [c for c in fake.calls if c[:2] == ("POST", "/rest/api/3/issueLink")
              and c[2]["type"]["name"] == "Blocks"]
    assert len(blocks) == len(BLOCKS)  # direction verified, no re-creation needed


def test_reset_keeps_seeded_comments_only(fake, tmp_path):
    seed_jira.main()
    state = json.loads((tmp_path / "seed_state.json").read_text())
    s3 = state["S3"]
    seeded = next(s for s in STORIES if s["id"] == "S3")["comments"]
    fake.comments[s3] = [{"id": str(i), "body": text_to_adf(t)} for i, t in enumerate(seeded)]
    fake.comments[s3].append({"id": "99", "body": text_to_adf("BA agent: clarifying questions...")})
    reset_demo.main()
    deletes = [c for c in fake.calls if c[0] == "DELETE"]
    assert deletes == [("DELETE", f"/rest/api/3/issue/{s3}/comment/99")]


def test_confluence_fills_real_keys(fake, tmp_path):
    seed_jira.main()
    seed_confluence.main()
    pages = [c[2] for c in fake.calls if c[:2] == ("POST", "/wiki/api/v2/pages")]
    assert len(pages) == 11
    bodies = " ".join(p["body"]["value"] for p in pages)
    assert "{{" not in bodies and re.search(r"PSA-\d+", bodies)


def test_planted_conflict_present():
    s3 = next(s for s in STORIES if s["id"] == "S3")
    assert "remove duplicates" in normalize(s3["description"])
    assert "acceptance criteria" not in normalize(s3["description"])
