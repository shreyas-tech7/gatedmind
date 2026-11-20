"""Chunk the documents and store each chunk with its access rules in SQLite.

Tables: people, docs, chunks (text and an optional embedding) and grants (one row per
chunk and principal). Folder rules are resolved when the index is built, so every chunk
carries the rules that apply to it. BM25 and the embedding matrix are built in memory
from the chunks table when the index opens.
"""

from __future__ import annotations

import json
import re
import sqlite3
from pathlib import Path

import numpy as np

from .bm25 import BM25, top_k
from .org import effective_grants, principals

SCHEMA = """
CREATE TABLE meta(key TEXT PRIMARY KEY, value TEXT);
CREATE TABLE people(id TEXT PRIMARY KEY, name TEXT, dept TEXT, role TEXT, projects TEXT);
CREATE TABLE docs(id TEXT PRIMARY KEY, title TEXT, folder TEXT, owner TEXT);
CREATE TABLE chunks(id INTEGER PRIMARY KEY, doc_id TEXT NOT NULL, ord INTEGER, text TEXT, emb BLOB);
CREATE TABLE grants(chunk_id INTEGER NOT NULL, principal TEXT NOT NULL);
CREATE INDEX grants_by_principal ON grants(principal, chunk_id);
"""
_SENT = re.compile(r"(?<=\.)\s+")
RRF_K = 60


def sentences(text: str) -> list[str]:
    return [s for s in _SENT.split(text.strip()) if s]


def chunk(text: str, size: int = 2) -> list[str]:
    s = sentences(text)
    return [" ".join(s[i : i + size]) for i in range(0, len(s), size)]


def build(org: dict, path: Path, embedder=None) -> Path:
    path = Path(path)
    path.unlink(missing_ok=True)
    con = sqlite3.connect(path)
    con.executescript(SCHEMA)
    con.execute("INSERT INTO meta VALUES ('seed', ?)", (str(org["seed"]),))
    con.execute("INSERT INTO meta VALUES ('embedder', ?)", (embedder.name if embedder else "",))
    for p in org["people"]:
        con.execute(
            "INSERT INTO people VALUES (?,?,?,?,?)",
            (p["id"], p["name"], p["dept"], p["role"], json.dumps(p["projects"])),
        )
    rows = []
    for d in org["docs"]:
        con.execute(
            "INSERT INTO docs VALUES (?,?,?,?)", (d["id"], d["title"], d["folder"], d["owner"])
        )
        grants = effective_grants(d, org["folders"])
        if not grants:
            raise ValueError(f"{d['id']} has no rules and no folder rules")
        for i, text in enumerate(chunk(d["text"])):
            rows.append((d["id"], i, text, grants))
    embs = embedder.embed([r[2] for r in rows]) if embedder else None
    for n, (doc_id, i, text, grants) in enumerate(rows):
        blob = embs[n].astype(np.float32).tobytes() if embs is not None else None
        cur = con.execute(
            "INSERT INTO chunks(doc_id, ord, text, emb) VALUES (?,?,?,?)", (doc_id, i, text, blob)
        )
        con.executemany(
            "INSERT INTO grants VALUES (?,?)", [(cur.lastrowid, g) for g in sorted(set(grants))]
        )
    con.commit()
    con.close()
    return path


class Index:
    def __init__(self, path: Path, embedder=None):
        self.con = sqlite3.connect(
            Path(path).resolve().as_uri() + "?mode=ro", uri=True, check_same_thread=False
        )
        rows = self.con.execute("SELECT id, doc_id, text, emb FROM chunks ORDER BY id").fetchall()
        self.chunk_ids = np.array([r[0] for r in rows], dtype=np.int64)
        self.row_of = {cid: i for i, cid in enumerate(self.chunk_ids.tolist())}
        self.doc_ids = [r[1] for r in rows]
        self.texts = [r[2] for r in rows]
        self.bm25 = BM25(self.texts)
        self.embedder = embedder
        self.emb = None
        if embedder is not None and rows and rows[0][3] is not None:
            self.emb = np.vstack([np.frombuffer(r[3], dtype=np.float32) for r in rows])
        self.people = {
            r[0]: {
                "id": r[0],
                "name": r[1],
                "dept": r[2],
                "role": r[3],
                "projects": json.loads(r[4]),
            }
            for r in self.con.execute("SELECT id, name, dept, role, projects FROM people")
        }
        self.titles = dict(self.con.execute("SELECT id, title FROM docs").fetchall())
        self.owners = dict(self.con.execute("SELECT id, owner FROM docs").fetchall())

    def principals(self, identity: str) -> set[str]:
        """Principals for a test identity. Unknown identities raise KeyError."""
        return principals(self.people[identity])

    def allowed_rows(self, identity: str) -> np.ndarray:
        """Rows of the chunks this identity may read, from the grants table in SQL."""
        ps = sorted(self.principals(identity))
        q = "SELECT DISTINCT chunk_id FROM grants WHERE principal IN ({})".format(  # noqa: S608 (only ? placeholders)
            ",".join("?" * len(ps))
        )
        ids = [r[0] for r in self.con.execute(q, ps)]
        return np.array(sorted(self.row_of[i] for i in ids), dtype=np.int64)

    def search(self, query: str, k: int, rows: np.ndarray | None = None, retriever="bm25"):
        """Top k chunk rows for the query, best first. `rows` limits the candidates."""
        cand = np.arange(len(self.texts)) if rows is None else rows
        if len(cand) == 0:
            return []
        if retriever == "bm25":
            return self._rank_bm25(query, cand, k)
        if retriever == "dense":
            return self._rank_dense(query, cand, k)
        if retriever == "hybrid":
            depth = max(50, k)
            fused: dict[int, float] = {}
            for ranked in (
                self._rank_bm25(query, cand, depth),
                self._rank_dense(query, cand, depth),
            ):
                for rank, row in enumerate(ranked):
                    fused[row] = fused.get(row, 0.0) + 1.0 / (RRF_K + rank + 1)
            return sorted(fused, key=lambda r: (-fused[r], r))[:k]
        raise ValueError(f"unknown retriever {retriever!r}")

    def _rank_bm25(self, query, cand, k):
        scores = self.bm25.scores(query)[cand]
        return [int(cand[i]) for i in top_k(scores, k)]

    def _rank_dense(self, query, cand, k):
        if self.emb is None:
            raise RuntimeError("this index has no embeddings")
        q = self.embedder.embed_query(query)
        scores = self.emb[cand] @ q
        return [int(cand[i]) for i in top_k(scores, k, positive_only=False)]

    def doc_text(self, doc_id: str) -> str:
        rows = self.con.execute(
            "SELECT text FROM chunks WHERE doc_id = ? ORDER BY ord", (doc_id,)
        ).fetchall()
        return " ".join(r[0] for r in rows)

    def doc_allowed(self, identity: str, doc_id: str) -> bool:
        ps = sorted(self.principals(identity))
        q = (
            "SELECT 1 FROM chunks c JOIN grants g ON g.chunk_id = c.id "  # noqa: S608 (only ? placeholders)
            "WHERE c.doc_id = ? AND g.principal IN ({}) LIMIT 1".format(",".join("?" * len(ps)))
        )
        return self.con.execute(q, [doc_id, *ps]).fetchone() is not None
