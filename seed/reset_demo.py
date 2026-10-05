"""Restore every seeded ticket to its original state (description, labels, comments).
Run before each practice run and before recording:  python -m seed.reset_demo"""
import json
import sys

from common.atlassian import ROOT, Atlassian, adf_to_text, normalize, text_to_adf
from seed.seed_data import STORIES

STATE_FILE = ROOT / "seed_state.json"


def main():
    if not STATE_FILE.exists():
        sys.exit("seed_state.json not found. Run 'python -m seed.seed_jira' first.")
    keys = json.loads(STATE_FILE.read_text())
    api = Atlassian()

    missing = []
    for story in STORIES:
        key = keys[story["id"]]
        try:
            api.put(f"/rest/api/3/issue/{key}", json={"fields": {
                "description": text_to_adf(story["description"]), "labels": story["labels"]}})
        except RuntimeError as err:
            if "-> 404" not in str(err):
                raise
            missing.append(key)
            print(f"  {key} not found (deleted?) - skipped")
            continue

        seeded = {normalize(c) for c in story.get("comments", [])}
        comments = api.get(f"/rest/api/3/issue/{key}/comment?maxResults=100")["comments"]
        removed = 0
        for c in comments:
            if normalize(adf_to_text(c["body"])) not in seeded:
                api.delete(f"/rest/api/3/issue/{key}/comment/{c['id']}")
                removed += 1
        print(f"  {key} reset" + (f" (removed {removed} comment(s))" if removed else ""))
    if missing:
        print(f"Done, but {len(missing)} ticket(s) are missing: run python -m seed.restore_ticket")
    else:
        print("Done. Tickets are back to the seeded state.")


if __name__ == "__main__":
    main()
