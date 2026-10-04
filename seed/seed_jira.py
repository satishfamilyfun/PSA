"""Seed the PSA Jira project.  Run from the repo root:  python -m seed.seed_jira"""
import json
import mimetypes
import sys

from common.atlassian import ROOT, Atlassian, env, text_to_adf
from seed.seed_data import BLOCKS, DEMO_TARGETS, EPICS, RELATES, STORIES

STATE_FILE = ROOT / "seed_state.json"


def pick_issue_types(api, project_key):
    project = api.get(f"/rest/api/3/project/{project_key}")
    names = {t["name"] for t in project.get("issueTypes", []) if not t.get("subtask")}
    story = "Story" if "Story" in names else "Task"
    epic = "Epic" if "Epic" in names else None
    print(f"Project {project_key} found. Using issue type '{story}'" + (", with an Epic." if epic else ", no Epic type."))
    return story, epic


def create_issue(api, fields):
    return api.post("/rest/api/3/issue", json={"fields": fields})["key"]


def link_blocks(api, blocker, blocked):
    """Create 'blocker blocks blocked', then verify the direction and fix it if Jira stored it reversed."""
    api.post("/rest/api/3/issueLink", json={
        "type": {"name": "Blocks"}, "inwardIssue": {"key": blocker}, "outwardIssue": {"key": blocked}})
    links = api.get(f"/rest/api/3/issue/{blocked}?fields=issuelinks")["fields"]["issuelinks"]
    for link in links:
        if link["type"]["name"] != "Blocks":
            continue
        if link.get("inwardIssue", {}).get("key") == blocker:
            return  # blocked issue shows "is blocked by <blocker>": correct
        if link.get("outwardIssue", {}).get("key") == blocker:
            api.delete(f"/rest/api/3/issueLink/{link['id']}")
            api.post("/rest/api/3/issueLink", json={
                "type": {"name": "Blocks"}, "inwardIssue": {"key": blocked}, "outwardIssue": {"key": blocker}})
            return


def main():
    if STATE_FILE.exists() and "--force" not in sys.argv:
        sys.exit(f"{STATE_FILE.name} exists, so the project looks seeded already. "
                 "Use 'python -m seed.reset_demo' to reset, or add --force to seed again.")

    api = Atlassian()
    project_key = env("JIRA_PROJECT_KEY")
    story_type, epic_type = pick_issue_types(api, project_key)
    keys = {}

    if epic_type:
        for epic in EPICS:
            try:
                key = create_issue(api, {
                    "project": {"key": project_key}, "issuetype": {"name": epic_type},
                    "summary": epic["summary"], "description": text_to_adf(epic["description"])})
                keys[epic["id"]] = key
                print(f"  {key}  [epic] {epic['summary']}")
            except RuntimeError as err:
                print(f"  Could not create epic '{epic['summary']}', continuing without it ({err})")

    for story in STORIES:
        fields = {
            "project": {"key": project_key}, "issuetype": {"name": story_type},
            "summary": story["summary"], "description": text_to_adf(story["description"]),
            "labels": story["labels"],
        }
        epic_key = keys.get(story.get("epic"))
        try:
            key = create_issue(api, {**fields, "parent": {"key": epic_key}} if epic_key else fields)
        except RuntimeError:
            key = create_issue(api, fields)  # some project types reject 'parent'
        keys[story["id"]] = key
        print(f"  {key}  {story['summary']}")

        for comment in story.get("comments", []):
            api.post(f"/rest/api/3/issue/{key}/comment", json={"body": text_to_adf(comment)})

        for rel_path in story.get("attachments", []):
            path = ROOT / rel_path
            with open(path, "rb") as fh:
                api.post(f"/rest/api/3/issue/{key}/attachments",
                         headers={"X-Atlassian-Token": "no-check"},
                         files={"file": (path.name, fh, mimetypes.guess_type(path.name)[0] or "application/octet-stream")})
            print(f"           attached {path.name}")

    for blocker, blocked in BLOCKS:
        link_blocks(api, keys[blocker], keys[blocked])
    for a, b in RELATES:
        api.post("/rest/api/3/issueLink", json={
            "type": {"name": "Relates"}, "inwardIssue": {"key": keys[a]}, "outwardIssue": {"key": keys[b]}})
    print(f"  Created {len(BLOCKS)} 'blocks' links and {len(RELATES)} 'relates' links.")

    STATE_FILE.write_text(json.dumps(keys, indent=2))
    print(f"\nSaved {STATE_FILE.name}. Demo targets:")
    for name, sid in DEMO_TARGETS.items():
        print(f"  {name}: {keys[sid]}")


if __name__ == "__main__":
    main()
