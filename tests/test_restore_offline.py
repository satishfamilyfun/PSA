"""Offline tests for seed.restore_ticket and the missing-ticket handling in seed.reset_demo."""
import json

import pytest

from seed import reset_demo, restore_ticket
from seed.seed_data import BLOCKS, EPICS, RELATES, STORIES


class FakeJira:
    """Minimal Jira with some issues deleted (GET/PUT on them returns 404)."""

    def __init__(self, deleted):
        self.deleted, self.calls, self.links, self.next = set(deleted), [], {}, 100

    def _missing(self, path):
        key = path.split("/")[5].split("?")[0] if path.startswith("/rest/api/3/issue/") else None
        if key in self.deleted:
            raise RuntimeError(f"GET {path} -> 404: Issue does not exist")

    def get(self, path, **kw):
        self.calls.append(("GET", path))
        self._missing(path)
        if path.startswith("/rest/api/3/project/"):
            return {"issueTypes": [{"name": n, "subtask": False} for n in ("Epic", "Story")]}
        if "fields=issuelinks" in path:
            return {"fields": {"issuelinks": self.links.get(path.split("/")[5].split("?")[0], [])}}
        if path.endswith("/comment?maxResults=100"):
            return {"comments": []}
        return {"fields": {"summary": "x"}}

    def post(self, path, json=None, **kw):
        self.calls.append(("POST", path, json))
        if path == "/rest/api/3/issue":
            self.next += 1
            return {"key": f"PSA-{self.next}"}
        if path == "/rest/api/3/issueLink" and json["type"]["name"] == "Blocks":
            self.links.setdefault(json["outwardIssue"]["key"], []).append(
                {"id": "1", "type": {"name": "Blocks"}, "inwardIssue": {"key": json["inwardIssue"]["key"]}})
        return {}

    def put(self, path, json=None, **kw):
        self.calls.append(("PUT", path, json))
        self._missing(path)

    def delete(self, path, **kw):
        self.calls.append(("DELETE", path))


@pytest.fixture
def state(tmp_path, monkeypatch):
    keys = {e["id"]: f"PSA-{i + 1}" for i, e in enumerate(EPICS)}
    keys.update({s["id"]: f"PSA-{i + 20}" for i, s in enumerate(STORIES)})
    path = tmp_path / "seed_state.json"
    path.write_text(json.dumps(keys))
    for module in (restore_ticket, reset_demo):
        monkeypatch.setattr(module, "STATE_FILE", path)
    monkeypatch.setattr(restore_ticket, "env", lambda name: "PSA")
    return path, keys


def use(monkeypatch, api, argv=("restore",)):
    for module in (restore_ticket, reset_demo):
        monkeypatch.setattr(module, "Atlassian", lambda: api)
    monkeypatch.setattr("sys.argv", list(argv))


def test_restores_deleted_story_with_everything(state, monkeypatch, capsys):
    path, keys = state
    s6 = next(s for s in STORIES if s["id"] == "S6")
    api = FakeJira({keys["S6"]})
    use(monkeypatch, api)
    restore_ticket.main()

    new = json.loads(path.read_text())
    assert new["S6"] == "PSA-101" and new["S5"] == keys["S5"]          # only S6 changed
    created = [c for c in api.calls if c[:2] == ("POST", "/rest/api/3/issue")]
    assert len(created) == 1 and created[0][2]["fields"]["parent"] == {"key": keys[s6["epic"]]}
    assert sum(1 for c in api.calls if c[1].endswith("PSA-101/comment")) == len(s6["comments"])
    assert sum(1 for c in api.calls if c[1].endswith("PSA-101/attachments")) == len(s6["attachments"])
    links = [c for c in api.calls if c[:2] == ("POST", "/rest/api/3/issueLink")]
    expected = sum(1 for a, b in BLOCKS + RELATES if "S6" in (a, b))
    assert len(links) == expected
    assert "S6 (was" in capsys.readouterr().out


def test_restores_deleted_epic_and_reparents_stories(state, monkeypatch):
    path, keys = state
    api = FakeJira({keys["E3"]})
    use(monkeypatch, api)
    restore_ticket.main()
    new_epic = json.loads(path.read_text())["E3"]
    reparented = [c for c in api.calls if c[0] == "PUT" and c[2] == {"fields": {"parent": {"key": new_epic}}}]
    assert len(reparented) == sum(1 for s in STORIES if s.get("epic") == "E3")


def test_check_only_reports(state, monkeypatch, capsys):
    path, keys = state
    api = FakeJira({keys["S3"]})
    use(monkeypatch, api, ("restore", "--check"))
    restore_ticket.main()
    assert "S3 (was" in capsys.readouterr().out
    assert not [c for c in api.calls if c[0] == "POST"]
    assert json.loads(path.read_text()) == keys


def test_nothing_missing(state, monkeypatch, capsys):
    use(monkeypatch, FakeJira(set()))
    restore_ticket.main()
    assert "Nothing to restore" in capsys.readouterr().out


def test_reset_skips_deleted_ticket(state, monkeypatch, capsys):
    path, keys = state
    use(monkeypatch, FakeJira({keys["S6"]}))
    reset_demo.main()
    out = capsys.readouterr().out
    assert f"{keys['S6']} not found" in out and "run python -m seed.restore_ticket" in out
