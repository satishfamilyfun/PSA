"""Publish kb/*.md to the Confluence space (creates pages, or updates them on re-run).
Run AFTER seed_jira (story placeholders are replaced with real Jira keys):
    python -m seed.seed_confluence"""
import json
import re
import sys

import markdown

from common.atlassian import ROOT, Atlassian, env

KB_DIR = ROOT / "kb"
STATE_FILE = ROOT / "seed_state.json"


def to_storage(md_text: str) -> tuple[str, str]:
    lines = md_text.strip().splitlines()
    title = lines[0].lstrip("# ").strip()
    body = markdown.markdown("\n".join(lines[1:]), extensions=["tables", "fenced_code"], output_format="xhtml")
    return title, body


def fill_keys(text: str, keys: dict) -> str:
    """Replace {{S9}}-style placeholders with the real Jira keys created by seed_jira."""
    return re.sub(r"\{\{(S\d+)\}\}", lambda m: keys.get(m.group(1), m.group(1)), text)


def main():
    if not STATE_FILE.exists():
        sys.exit("seed_state.json not found. Run 'python -m seed.seed_jira' first, then this script.")
    keys = json.loads(STATE_FILE.read_text())
    api = Atlassian()
    space_key = env("CONFLUENCE_SPACE_KEY")
    spaces = api.get(f"/wiki/api/v2/spaces?keys={space_key}")["results"]
    if not spaces:
        sys.exit(f"Confluence space '{space_key}' not found. Check CONFLUENCE_SPACE_KEY in .env.")
    space_id = spaces[0]["id"]

    for path in sorted(KB_DIR.glob("*.md")):
        title, body = to_storage(fill_keys(path.read_text(encoding="utf-8"), keys))
        found = api.get("/wiki/api/v2/pages", params={"space-id": space_id, "title": title})["results"]
        payload = {"status": "current", "title": title,
                   "body": {"representation": "storage", "value": body}}
        if found:
            page = api.get(f"/wiki/api/v2/pages/{found[0]['id']}")
            api.put(f"/wiki/api/v2/pages/{page['id']}", json={
                **payload, "id": page["id"], "version": {"number": page["version"]["number"] + 1}})
            print(f"  updated  {title}")
        else:
            api.post("/wiki/api/v2/pages", json={**payload, "spaceId": space_id})
            print(f"  created  {title}")
    print("Knowledge base published.")


if __name__ == "__main__":
    main()
