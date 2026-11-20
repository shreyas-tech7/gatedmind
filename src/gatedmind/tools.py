"""The three tools behind the MCP server: search, get_doc and who_knows.

Every tool takes a test identity (a person ID such as "p007") and always pre-filters with the
access rules (mode 1). The identity is a test token. It is not authentication: anyone who can
call the server can claim any identity.
"""

from __future__ import annotations

import json
from collections import Counter

from .audit import AuditLog
from .index import Index

MAX_QUERY = 500
ID_SCHEMA = {
    "type": "string",
    "description": "Test identity, a person ID like p007. Not authentication.",
}
TOOLS = [
    {
        "name": "search",
        "description": "Search the documents the identity may read. Returns IDs, titles and snippets.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "identity": ID_SCHEMA,
                "query": {"type": "string", "maxLength": MAX_QUERY},
                "k": {"type": "integer", "minimum": 1, "maximum": 10, "default": 4},
            },
            "required": ["identity", "query"],
            "additionalProperties": False,
        },
    },
    {
        "name": "get_doc",
        "description": "Return the full text of one document if the identity may read it.",
        "inputSchema": {
            "type": "object",
            "properties": {"identity": ID_SCHEMA, "doc_id": {"type": "string", "maxLength": 16}},
            "required": ["identity", "doc_id"],
            "additionalProperties": False,
        },
    },
    {
        "name": "who_knows",
        "description": "Name the owners of readable documents about a topic.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "identity": ID_SCHEMA,
                "topic": {"type": "string", "maxLength": MAX_QUERY},
            },
            "required": ["identity", "topic"],
            "additionalProperties": False,
        },
    },
]
NOT_FOUND = "document not found or not allowed"


class ToolError(Exception):
    pass


class Tools:
    def __init__(self, index: Index, audit: AuditLog | None = None):
        self.index, self.audit = index, audit

    def _identity(self, args: dict) -> str:
        ident = args.get("identity")
        if not isinstance(ident, str) or ident not in self.index.people:
            raise ToolError("unknown identity")
        return ident

    def _text(self, args: dict, key: str) -> str:
        v = args.get(key)
        if not isinstance(v, str) or not v.strip() or len(v) > MAX_QUERY:
            raise ToolError(f"{key} must be a non-empty string of at most {MAX_QUERY} characters")
        return v

    def _log(self, ident, action, query, docs, denied):
        if self.audit:
            self.audit.write(
                identity=ident,
                action=action,
                query=query,
                returned_doc_ids=docs,
                denied_chunks=denied,
            )

    def call(self, name: str, args: dict | None) -> tuple[str, bool]:
        """Run a tool. Returns (text, is_error)."""
        args = dict(args or {})
        try:
            fn = {"search": self.search, "get_doc": self.get_doc, "who_knows": self.who_knows}.get(
                name
            )
            if fn is None:
                raise ToolError(f"unknown tool {name!r}")
            return json.dumps(fn(args), indent=1), False
        except ToolError as e:
            return str(e), True
        except Exception:  # fail closed and keep internal details out of the reply
            return "internal error", True

    def search(self, args: dict) -> list[dict]:
        ident, query = self._identity(args), self._text(args, "query")
        k = args.get("k", 4)
        if not isinstance(k, int) or isinstance(k, bool) or not 1 <= k <= 10:
            raise ToolError("k must be an integer from 1 to 10")
        rows = self.index.allowed_rows(ident)
        hits = self.index.search(query, k, rows=rows)
        out, seen = [], set()
        for h in hits:
            d = self.index.doc_ids[h]
            if d not in seen:
                seen.add(d)
                out.append(
                    {"doc_id": d, "title": self.index.titles[d], "snippet": self.index.texts[h]}
                )
        self._log(
            ident, "search", query, [r["doc_id"] for r in out], len(self.index.texts) - len(rows)
        )
        return out

    def get_doc(self, args: dict) -> dict:
        ident = self._identity(args)
        doc_id = args.get("doc_id")
        ok = isinstance(doc_id, str) and doc_id in self.index.titles
        ok = ok and self.index.doc_allowed(ident, doc_id)
        self._log(ident, "get_doc", str(doc_id), [doc_id] if ok else [], 0 if ok else 1)
        if not ok:
            raise ToolError(NOT_FOUND)  # same answer for missing and forbidden
        return {
            "doc_id": doc_id,
            "title": self.index.titles[doc_id],
            "text": self.index.doc_text(doc_id),
        }

    def who_knows(self, args: dict) -> list[dict]:
        ident, topic = self._identity(args), self._text(args, "topic")
        rows = self.index.allowed_rows(ident)
        docs = list(
            dict.fromkeys(self.index.doc_ids[h] for h in self.index.search(topic, 20, rows=rows))
        )
        owners = Counter(self.index.owners[d] for d in docs)
        out = []
        for pid, n in owners.most_common(5):
            p = self.index.people[pid]
            out.append({"person_id": pid, "name": p["name"], "dept": p["dept"], "matching_docs": n})
        self._log(ident, "who_knows", topic, docs, len(self.index.texts) - len(rows))
        return out
