"""Tool registry: each tool is (definition, handler).

Handlers receive the tool input dict + a `context` dict with run-scoped state
(user, project, etc.) and must return a JSON-serializable result.

SECURITY:
- query_db is wrapped in an atomic block that ALWAYS rolls back, so even if
  the model emits a write statement nothing persists. Additionally we reject
  any statement that isn't a single SELECT/WITH.
- read_pdf only accepts paths under MEDIA_ROOT.
- web_fetch limits response size and disallows private network ranges.
"""
from __future__ import annotations

import ipaddress
import re
from pathlib import Path
from typing import Any, Callable
from urllib.parse import urlparse

from django.conf import settings
from django.db import connection, transaction


ToolHandler = Callable[[dict, dict], Any]
_REGISTRY: dict[str, tuple[dict, ToolHandler]] = {}


def register(definition: dict):
    def deco(fn: ToolHandler):
        _REGISTRY[definition["name"]] = (definition, fn)
        return fn
    return deco


def get_definitions(names: list[str] | None = None) -> list[dict]:
    if names is None:
        return [d for d, _ in _REGISTRY.values()]
    return [_REGISTRY[n][0] for n in names if n in _REGISTRY]


def run_tool(name: str, tool_input: dict, context: dict) -> Any:
    if name not in _REGISTRY:
        raise ValueError(f"Unknown tool: {name}")
    _, handler = _REGISTRY[name]
    return handler(tool_input, context)


# --- query_db -----------------------------------------------------------------

_SELECT_RE = re.compile(r"^\s*(SELECT|WITH)\b", re.IGNORECASE)


@register({
    "name": "query_db",
    "description": (
        "Run a read-only SQL query against the ERP database. "
        "Only SELECT / WITH statements are allowed. Always rolled back."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "sql": {"type": "string", "description": "Single SELECT/WITH statement."},
            "limit": {"type": "integer", "description": "Hard row cap (default 100, max 1000)."},
        },
        "required": ["sql"],
    },
})
def _query_db(inp: dict, ctx: dict) -> dict:
    sql = inp["sql"].strip().rstrip(";")
    if ";" in sql:
        raise ValueError("Multiple statements are not allowed.")
    if not _SELECT_RE.match(sql):
        raise ValueError("Only SELECT/WITH statements are allowed.")
    limit = min(int(inp.get("limit") or 100), 1000)

    with transaction.atomic():
        sid = transaction.savepoint()
        try:
            with connection.cursor() as cur:
                cur.execute(f"SELECT * FROM ({sql}) _q LIMIT %s", [limit])
                cols = [c[0] for c in cur.description]
                rows = [dict(zip(cols, r)) for r in cur.fetchall()]
        finally:
            transaction.savepoint_rollback(sid)
    return {"columns": cols, "rows": rows, "row_count": len(rows)}


# --- read_pdf -----------------------------------------------------------------

@register({
    "name": "read_pdf",
    "description": "Extract text from a PDF stored under MEDIA_ROOT. Returns text + page count.",
    "input_schema": {
        "type": "object",
        "properties": {
            "path": {"type": "string", "description": "Path relative to MEDIA_ROOT."},
            "max_pages": {"type": "integer", "description": "Default 20."},
        },
        "required": ["path"],
    },
})
def _read_pdf(inp: dict, ctx: dict) -> dict:
    import pdfplumber  # already in requirements
    media = Path(settings.MEDIA_ROOT).resolve()
    target = (media / inp["path"]).resolve()
    if not str(target).startswith(str(media)):
        raise ValueError("Path escapes MEDIA_ROOT.")
    if not target.exists():
        raise FileNotFoundError(str(target))
    max_pages = int(inp.get("max_pages") or 20)
    pages = []
    with pdfplumber.open(target) as pdf:
        for i, page in enumerate(pdf.pages[:max_pages]):
            pages.append(page.extract_text() or "")
        total = len(pdf.pages)
    return {"text": "\n\n".join(pages), "pages_read": len(pages), "total_pages": total}


# --- web_fetch ---------------------------------------------------------------

@register({
    "name": "web_fetch",
    "description": "Fetch a public URL (HTTP/HTTPS). Returns up to 200KB of text. Blocks private networks.",
    "input_schema": {
        "type": "object",
        "properties": {"url": {"type": "string"}},
        "required": ["url"],
    },
})
def _web_fetch(inp: dict, ctx: dict) -> dict:
    import socket
    import urllib.request
    url = inp["url"]
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise ValueError("Only http/https URLs are allowed.")
    host = parsed.hostname or ""
    try:
        ip = ipaddress.ip_address(socket.gethostbyname(host))
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise ValueError("Private network addresses are not allowed.")
    except (socket.gaierror, ValueError) as e:
        raise ValueError(f"Could not resolve host: {e}")

    req = urllib.request.Request(url, headers={"User-Agent": "ConstructionERP-Agent/1.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        data = resp.read(200_000)
    return {"url": url, "text": data.decode("utf-8", errors="replace")}


# --- git_diff ----------------------------------------------------------------

@register({
    "name": "git_diff",
    "description": "Show git diff between two refs (default: HEAD vs main). Read-only.",
    "input_schema": {
        "type": "object",
        "properties": {
            "base": {"type": "string", "description": "Base ref. Default 'main'."},
            "head": {"type": "string", "description": "Head ref. Default 'HEAD'."},
            "path": {"type": "string", "description": "Optional path filter."},
        },
    },
})
def _git_diff(inp: dict, ctx: dict) -> dict:
    import subprocess
    base = inp.get("base") or "main"
    head = inp.get("head") or "HEAD"
    cmd = ["git", "diff", f"{base}...{head}"]
    if inp.get("path"):
        cmd += ["--", inp["path"]]
    out = subprocess.run(cmd, capture_output=True, text=True, timeout=30, cwd=settings.BASE_DIR)
    return {"diff": out.stdout[:200_000], "stderr": out.stderr[:2000]}
