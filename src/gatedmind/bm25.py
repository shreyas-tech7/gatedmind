"""BM25 (Okapi) written from scratch with numpy. No stemming. A short stop list."""

from __future__ import annotations

import math
import re
from collections import Counter, defaultdict

import numpy as np

_TOKEN = re.compile(r"[a-z0-9]+")
STOP = frozenset(
    "a an and are as at be by for from has have in is it its of on or that the this to "
    "was were will with you your can do does not".split()
)


def tokenize(text: str) -> list[str]:
    return [t for t in _TOKEN.findall(text.lower()) if t not in STOP]


class BM25:
    def __init__(self, texts: list[str], k1: float = 1.2, b: float = 0.75):
        self.k1, self.b = k1, b
        self.n = len(texts)
        docs = [tokenize(t) for t in texts]
        lengths = np.array([len(d) for d in docs], dtype=np.float64)
        self.avgdl = float(lengths.mean()) if self.n else 0.0
        postings: dict[str, list[tuple[int, int]]] = defaultdict(list)
        for i, d in enumerate(docs):
            for term, tf in Counter(d).items():
                postings[term].append((i, tf))
        norm = k1 * (1 - b + b * lengths / (self.avgdl or 1.0))
        self.index: dict[str, tuple[np.ndarray, np.ndarray]] = {}
        for term, plist in postings.items():
            ids = np.fromiter((p[0] for p in plist), dtype=np.int64, count=len(plist))
            tf = np.fromiter((p[1] for p in plist), dtype=np.float64, count=len(plist))
            df = len(plist)
            idf = math.log(1 + (self.n - df + 0.5) / (df + 0.5))
            self.index[term] = (ids, idf * tf * (k1 + 1) / (tf + norm[ids]))

    def scores(self, query: str) -> np.ndarray:
        out = np.zeros(self.n, dtype=np.float64)
        for term in tokenize(query):
            hit = self.index.get(term)
            if hit is not None:
                out[hit[0]] += hit[1]
        return out

    def search(self, query: str, k: int) -> list[int]:
        return top_k(self.scores(query), k)


def top_k(scores: np.ndarray, k: int, positive_only: bool = True) -> list[int]:
    """Indexes of the k highest scores, best first. Ties break by lower index.

    With positive_only, chunks that score zero or less are dropped (BM25 non-matches).
    """
    k = min(k, len(scores))
    if k == 0:
        return []
    idx = np.argsort(-np.asarray(scores), kind="stable")[:k]
    return [int(i) for i in idx if not positive_only or scores[i] > 0]
