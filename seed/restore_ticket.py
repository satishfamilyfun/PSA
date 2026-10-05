"""Recreate seeded tickets that were deleted from Jira (Jira Cloud has no recycle bin for issues).

    python -m seed.restore_ticket            # find and recreate every deleted seeded ticket
    python -m seed.restore_ticket --check    # only report which tickets are missing

A recreated ticket gets a NEW key (Jira never reuses keys). Its description, labels, comments,
attachments, epic and dependency links come from seed_data.py, and seed_state.json is updated.
Afterwards run `python -m seed.seed_confluence` so the knowledge base cites the new key.
"""
import json
import mimetypes
import sys

from common.atlassian import ROOT, Atlassian, env, text_to_adf
from seed.seed_data import BLOCKS, EPICS, RELATES, STORIES
from seed.seed_jira import create_issue, link_blocks, pick_issue_types

STATE_FILE = ROOT / "seed_state.json"


def exists(api: Atlassian, key: str) -> bool:
    try:
        api.get(f"/rest/api/3/issue/{key}?fields=summary")
        return True
    except RuntimeError as err:
        if "-> 404" in str(err):
            return False
        raise


def recreate_epic(api, epic, project_key, epic_type) -> str:
    return create_issue(api, {"project": {"key": project_key}, "issuetype": {"name": epic_type},
                              "summary": epic["summary"], "description": text_to_adf(epic["description"])})


def recreate_story(api, story, project_key, story_type, epic_key) -> str:
    fields = {"project": {"key": project_key}, "issuetype": {"name": story_type},
              "summary": story["summary"], "description": text_to_adf(story["description"]),
              "labels": story["labels"]}
    try:
        key = create_issue(api, {**fields, "parent": {"key": epic_key}} if epic_key else fields)
    except RuntimeError:
        key = create_issue(api, fields)
    for comment in story.get("comments", []):
        api.post(f"/rest/api/3/issue/{key}/comment", json={"body": text_to_adf(comment)})
    for rel_path in story.get("attachments", []):
        path = ROOT / rel_path
        with open(path, "rb") as fh:
            api.post(f"/rest/api/3/issue/{key}/attachments", headers={"X-Atlassian-Token": "no-check"},
                     files={"file": (path.name, fh, mimetypes.guess_type(path.name)[0] or "application/octet-stream")})
    return key


def main():
    if not STATE_FILE.exists():
        sys.exit("seed_state.json not found: the project was never seeded. Run python -m seed.seed_jira.")
    keys = json.loads(STATE_FILE.read_text())
    api = Atlassian()

    missing = [sid for sid, key in keys.items() if not exists(api, key)]
    if not missing:
        print("All seeded tickets exist. Nothing to restore.")
        return
    print("Missing from Jira: " + ", ".join(f"{sid} (was {keys[sid]})" for sid in missing))
    if "--check" in sys.argv:
        return

    project_key = env("JIRA_PROJECT_KEY")
    story_type, epic_type = pick_issue_types(api, project_key)
    old = {sid: keys[sid] for sid in missing}

    # Epics first, so recreated stories can be placed under them
    for epic in EPICS:
        if epic["id"] in missing and epic_type:
            keys[epic["id"]] = recreate_epic(api, epic, project_key, epic_type)
            print(f"  {epic['id']}: {old[epic['id']]} -> {keys[epic['id']]}  [epic] {epic['summary']}")
            for story in STORIES:  # move surviving stories back under the new epic
                if story.get("epic") == epic["id"] and story["id"] not in missing:
                    try:
                        api.put(f"/rest/api/3/issue/{keys[story['id']]}",
                                json={"fields": {"parent": {"key": keys[epic['id']]}}})
                    except RuntimeError as err:
                        print(f"    could not re-parent {keys[story['id']]}: {err}")

    for story in STORIES:
        if story["id"] in missing:
            keys[story["id"]] = recreate_story(api, story, project_key, story_type, keys.get(story.get("epic")))
            print(f"  {story['id']}: {old[story['id']]} -> {keys[story['id']]}  {story['summary']}")

    restored = 0
    for blocker, blocked in BLOCKS:
        if blocker in missing or blocked in missing:
            link_blocks(api, keys[blocker], keys[blocked])
            restored += 1
    for a, b in RELATES:
        if a in missing or b in missing:
            api.post("/rest/api/3/issueLink", json={
                "type": {"name": "Relates"}, "inwardIssue": {"key": keys[a]}, "outwardIssue": {"key": keys[b]}})
            restored += 1
    print(f"  Restored {restored} link(s).")

    STATE_FILE.write_text(json.dumps(keys, indent=2))
    print("\nseed_state.json updated. Next:")
    print("  python -m seed.seed_confluence   (knowledge base pages will cite the new keys)")
    print("  Use the new keys in your commands and in the recording script.")


if __name__ == "__main__":
    main()
