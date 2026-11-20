"""Audit log: one JSON line per query. It stores IDs and counts, never document text.

The query itself is stored as a SHA-256 hash, because a question can quote a document.
"""

from __future__ import annotations

import hashlib
import json
import time
from pathlib import Path


class AuditLog:
    def __init__(self, path: Path):
        self.path = Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def write(
        self,
        *,
        identity: str,
        action: str,
        query: str,
        returned_doc_ids: list[str],
        denied_chunks: int,
        mode: str = "prefilter",
    ) -> dict:
        entry = {
            "ts": round(time.time(), 3),
            "identity": identity,
            "action": action,
            "mode": mode,
            "query_sha256": hashlib.sha256(query.encode()).hexdigest(),
            "returned_doc_ids": list(returned_doc_ids),
            "denied_chunks": int(denied_chunks),
        }
        with self.path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(entry, sort_keys=True) + "\n")
        return entry
