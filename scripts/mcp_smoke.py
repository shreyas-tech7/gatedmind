"""MCP smoke test with the official client: start the server over stdio, list the tools and
call each tool once with an allowed identity and once with a forbidden one.

    python scripts/mcp_smoke.py [--index PATH]   (builds the seed 1 index when no path is given)
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import anyio
from mcp import Client, StdioServerParameters

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))


def plan(index_path: Path) -> list[tuple[str, dict, str]]:
    """Pick a restricted document, one person who may read it and one who may not."""
    from gatedmind.index import Index

    ix = Index(index_path)
    for doc_id in sorted(ix.titles):
        allowed = [p for p in sorted(ix.people) if ix.doc_allowed(p, doc_id)]
        denied = [p for p in sorted(ix.people) if not ix.doc_allowed(p, doc_id)]
        if allowed and denied and len(allowed) < 10:
            break
    title = ix.titles[doc_id]
    a, d = allowed[0], denied[0]
    calls = []
    for who, tag in ((a, "allowed"), (d, "forbidden")):
        calls.append(("search", {"identity": who, "query": title, "k": 3}, tag))
        calls.append(("get_doc", {"identity": who, "doc_id": doc_id}, tag))
        calls.append(("who_knows", {"identity": who, "topic": title}, tag))
    return [(n, args, tag, doc_id, ix.owners[doc_id]) for n, args, tag in calls]


async def smoke(index_path: Path, audit: Path | None = None) -> dict:
    args = ["-m", "gatedmind.cli", "serve", "--index", str(index_path)]
    if audit:
        args += ["--audit", str(audit)]
    params = StdioServerParameters(command=sys.executable, args=args)
    out = {"tools": [], "calls": []}
    async with Client(params, read_timeout_seconds=60) as client:
        listed = await client.list_tools()
        out["tools"] = sorted(t.name for t in listed.tools)
        for name, a, tag, doc_id, owner in plan(index_path):
            r = await client.call_tool(name, a)
            text = "".join(c.text for c in r.content if getattr(c, "type", "") == "text")
            out["calls"].append(
                {
                    "tool": name,
                    "args": a,
                    "who": tag,
                    "target": doc_id,
                    "owner": owner,
                    "is_error": bool(r.is_error),
                    "text": text,
                }
            )
    return out


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", type=Path)
    ap.add_argument("--audit", type=Path)
    a = ap.parse_args()
    if a.index is None:
        from gatedmind.cli import _ensure

        a.index = _ensure(1)
    res = anyio.run(smoke, a.index, a.audit)
    print("tools:", ", ".join(res["tools"]))
    for c in res["calls"]:
        body = c["text"] if len(c["text"]) < 400 else c["text"][:400] + " ..."
        print(f"\n> {c['tool']} as {c['args']['identity']} ({c['who']}), error={c['is_error']}")
        print(body)
    ok = res["tools"] == ["get_doc", "search", "who_knows"]
    for c in res["calls"]:
        allowed = c["who"] == "allowed"
        if c["tool"] == "get_doc":
            ok &= c["is_error"] != allowed
        elif c["tool"] == "search":
            ok &= not c["is_error"] and allowed == (f'"{c["target"]}"' in c["text"])
        else:  # who_knows names the owner for the allowed identity
            ok &= not c["is_error"] and (not allowed or f'"{c["owner"]}"' in c["text"])
    print("\nsmoke test:", "PASS" if ok else "FAIL")
    print(json.dumps({"pass": ok}))
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
