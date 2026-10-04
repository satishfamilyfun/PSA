"""Thin Jira/Confluence Cloud client shared by the seed scripts and (Day 2) the agent."""
import os
import sys
from pathlib import Path

import requests
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
load_dotenv(ROOT / ".env")


def env(name: str) -> str:
    value = os.getenv(name, "").strip()
    if not value:
        sys.exit(f"Missing {name} in .env (copy .env.example to .env and fill it in).")
    return value


class Atlassian:
    def __init__(self):
        self.base = env("ATLASSIAN_BASE_URL").rstrip("/")
        self.session = requests.Session()
        self.session.auth = (env("ATLASSIAN_EMAIL"), env("ATLASSIAN_API_TOKEN"))
        self.session.headers.update({"Accept": "application/json"})

    def request(self, method: str, path: str, ok=(200, 201, 204), **kwargs):
        resp = self.session.request(method, f"{self.base}{path}", timeout=30, **kwargs)
        if resp.status_code not in ok:
            raise RuntimeError(f"{method} {path} -> {resp.status_code}: {resp.text[:500]}")
        return resp.json() if resp.content and "json" in resp.headers.get("Content-Type", "") else None

    def get(self, path, **kw):
        return self.request("GET", path, **kw)

    def post(self, path, **kw):
        return self.request("POST", path, **kw)

    def put(self, path, **kw):
        return self.request("PUT", path, **kw)

    def delete(self, path, **kw):
        return self.request("DELETE", path, **kw)


# ---------- Atlassian Document Format (Jira v3 rich text) ----------

def text_to_adf(text: str) -> dict:
    """Convert simple text to ADF. Supports '## heading', '- bullet' and blank-line paragraphs."""
    content, para, bullets = [], [], []

    def flush_para():
        if para:
            content.append({"type": "paragraph", "content": [{"type": "text", "text": " ".join(para)}]})
            para.clear()

    def flush_bullets():
        if bullets:
            content.append({
                "type": "bulletList",
                "content": [
                    {"type": "listItem",
                     "content": [{"type": "paragraph", "content": [{"type": "text", "text": b}]}]}
                    for b in bullets
                ],
            })
            bullets.clear()

    for raw in text.strip().splitlines():
        line = raw.strip()
        if not line:
            flush_para(); flush_bullets()
        elif line.startswith("## "):
            flush_para(); flush_bullets()
            content.append({"type": "heading", "attrs": {"level": 3},
                            "content": [{"type": "text", "text": line[3:]}]})
        elif line.startswith("- "):
            flush_para()
            bullets.append(line[2:])
        else:
            flush_bullets()
            para.append(line)
    flush_para(); flush_bullets()
    return {"type": "doc", "version": 1, "content": content or [{"type": "paragraph", "content": []}]}


def adf_to_text(node) -> str:
    """Flatten ADF back to plain text (used for comparisons and for feeding the LLM)."""
    if node is None:
        return ""
    if isinstance(node, str):
        return node
    if node.get("type") == "text":
        return node.get("text", "")
    parts = [adf_to_text(child) for child in node.get("content", [])]
    sep = "\n" if node.get("type") in ("doc", "bulletList", "orderedList", "listItem") else ""
    text = sep.join(p for p in parts if p)
    if node.get("type") == "listItem":
        text = "- " + text
    return text


def normalize(text: str) -> str:
    return " ".join(text.replace("- ", " ").split()).lower()
