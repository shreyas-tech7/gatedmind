"""The four enforcement modes.

1 prefilter:  apply the access rules inside the retrieval query. The model sees allowed text only.
2 postfilter: retrieve first, then drop forbidden chunks before the model sees anything.
3 redact:     the model sees everything. Forbidden text is removed from the answer afterwards.
4 none:       the control. No enforcement at all.
"""

from __future__ import annotations

import time
from dataclasses import dataclass

from . import model
from .index import Index, sentences

MODES = ["prefilter", "postfilter", "redact", "none"]
NUMBER = {"prefilter": 1, "postfilter": 2, "redact": 3, "none": 4}


@dataclass
class Result:
    answer: str
    cited: list[str]
    context_rows: list[int]
    denied_chunks: int
    latency_ms: float


def redact(answer: str, forbidden_docs: set[str], forbidden_text: list[str]) -> str:
    """Drop lines that cite a forbidden document or quote a forbidden sentence word for word."""
    banned = {s for t in forbidden_text for s in sentences(t)}
    keep = []
    for line in answer.splitlines():
        ids = model.cited(line)
        if any(i in forbidden_docs for i in ids):
            continue
        body = line.split("] ", 1)[1] if ids else line
        if body in banned:
            continue
        keep.append(line)
    return "\n".join(keep) if keep else model.NOTHING


def run(index: Index, identity: str, query: str, mode: str, k: int = 4, retriever="bm25") -> Result:
    start = time.perf_counter()
    if mode not in MODES:
        raise ValueError(f"unknown mode {mode!r}")
    index.principals(identity)  # unknown identity raises KeyError in every mode
    if mode == "prefilter":
        rows = index.allowed_rows(identity)
        hits = index.search(query, k, rows=rows, retriever=retriever)
        denied = len(index.texts) - len(rows)
        forbidden: list[int] = []
    else:
        hits = index.search(query, k, retriever=retriever)
        forbidden = []
        if mode != "none":
            allowed = set(index.allowed_rows(identity).tolist())
            forbidden = [h for h in hits if h not in allowed]
        denied = len(forbidden)
        if mode == "postfilter":
            hits = [h for h in hits if h not in forbidden]
    ctx = [(index.doc_ids[h], index.texts[h]) for h in hits]
    text = model.answer(query, ctx)
    if mode == "redact" and forbidden:
        text = redact(
            text, {index.doc_ids[h] for h in forbidden}, [index.texts[h] for h in forbidden]
        )
    ms = (time.perf_counter() - start) * 1000
    return Result(text, model.cited(text), hits, denied, ms)
