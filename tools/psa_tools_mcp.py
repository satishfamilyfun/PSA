"""psa MCP server: deterministic ticket context for the SDLC agents.

Why it exists: the official Atlassian MCP server cannot download attachments, and gathering
a ticket, its comments, its linked tickets and their comments takes many separate calls.
One call here returns everything as Markdown and saves attachments to disk so Claude Code
can open them (images are viewed with the Read tool).

Registered in .mcp.json as server "psa", so the tool is mcp__psa__get_ticket_bundle.
"""
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from mcp.server.mcpserver import MCPServer  # noqa: E402

from common.atlassian import Atlassian, adf_to_text  # noqa: E402

RUNS = ROOT / "runs"
TEXT_LIMIT = 4000
FIELDS = "summary,description,status,labels,issuetype,parent,issuelinks,attachment,comment"

server = MCPServer("psa", instructions="Ticket context for the PSA SDLC agents.")


def _comments(issue: dict) -> list[str]:
    items = issue["fields"].get("comment", {}).get("comments", [])
    return [f"- {c['author']['displayName']} ({c['created'][:10]}): {adf_to_text(c['body'])}" for c in items]


def _download(api: Atlassian, key: str, att: dict) -> str:
    folder = RUNS / "attachments" / key
    folder.mkdir(parents=True, exist_ok=True)
    path = folder / re.sub(r"[^\w.\-]", "_", att["filename"])
    resp = api.session.get(att["content"], timeout=60)
    resp.raise_for_status()
    path.write_bytes(resp.content)
    mime = att.get("mimeType", "")
    line = f"- **{att['filename']}** ({mime}, {att.get('size', 0)} bytes) saved to `{path}`"
    if mime.startswith("image/"):
        return line + "\n  This is an image. Open it with the Read tool and describe what it shows."
    if mime.startswith("text/") or path.suffix in (".txt", ".md", ".csv", ".json"):
        text = path.read_text(encoding="utf-8", errors="replace")[:TEXT_LIMIT]
        return line + f"\n\n```\n{text}\n```"
    return line


def _record_active(key: str) -> None:
    """Remember which ticket is under review; the guard hook only allows writes to it."""
    RUNS.mkdir(exist_ok=True)
    active_file = RUNS / "active_ticket.json"
    current = {}
    if active_file.exists():
        try:
            current = json.loads(active_file.read_text())
        except json.JSONDecodeError:
            current = {}
    if current.get("key") != key:
        current = {"key": key, "role": current.get("role", "unknown"),
                   "started_at": datetime.now(timezone.utc).isoformat()}
    active_file.write_text(json.dumps(current, indent=2))


def build_bundle(api: Atlassian, issue_key: str) -> str:
    key = issue_key.strip().upper()
    issue = api.get(f"/rest/api/3/issue/{key}?fields={FIELDS}")
    f = issue["fields"]
    _record_active(key)

    out = [f"# {key}: {f['summary']}",
           f"- Type: {f['issuetype']['name']}  |  Status: {f['status']['name']}",
           f"- Labels: {', '.join(f.get('labels') or []) or '(none)'}"]
    if f.get("parent"):
        out.append(f"- Epic: {f['parent']['key']} {f['parent']['fields']['summary']}")
    out += ["", "## Description", adf_to_text(f.get("description")) or "(empty)",
            "", "## Comments", *(_comments(issue) or ["(none)"])]

    out += ["", "## Attachments"]
    atts = f.get("attachment") or []
    out += [_download(api, key, a) for a in atts] or ["(none)"]

    out += ["", "## Linked tickets"]
    links = f.get("issuelinks") or []
    if not links:
        out.append("(none)")
    for link in links:
        if "inwardIssue" in link:
            other, relation = link["inwardIssue"], link["type"]["inward"]
        else:
            other, relation = link["outwardIssue"], link["type"]["outward"]
        status = other["fields"]["status"]["name"]
        out.append(f"\n### {key} {relation} {other['key']}: {other['fields']['summary']} [{status}]")
        # Full detail only for tickets that block this one or are related to it
        if relation in ("is blocked by", "relates to"):
            linked = api.get(f"/rest/api/3/issue/{other['key']}?fields=description,comment,labels")
            out.append(adf_to_text(linked["fields"].get("description")) or "(no description)")
            comments = _comments(linked)
            if comments:
                out += ["Comments:", *comments]
    return "\n".join(out)


@server.tool()
def get_ticket_bundle(issue_key: str) -> str:
    """Return a Jira ticket with description, comments, attachments (downloaded locally),
    and linked tickets. Blocking and related tickets include their description and comments,
    so open questions in dependencies are visible. Use this first when reviewing a ticket."""
    try:
        return build_bundle(Atlassian(), issue_key)
    except SystemExit as err:  # missing .env values
        return f"Configuration error: {err}"
    except Exception as err:  # surface errors to the agent instead of crashing the server
        return f"Error fetching {issue_key}: {err}"


if __name__ == "__main__":
    server.run()
