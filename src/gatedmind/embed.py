"""Embedders. The hash embedder is a fake for tests. MiniLM runs through FastEmbed.

Hugging Face can be blocked on the build machine, so FastEmbed loads an ONNX export of
all-MiniLM-L6-v2 from a local folder that `scripts/fetch_model.py` fills and checks by hash.
"""

from __future__ import annotations

import hashlib
import os
from pathlib import Path

import numpy as np

from .bm25 import tokenize

ROOT = Path(__file__).resolve().parents[2]
MINILM = {
    "fastembed_name": "sentence-transformers/all-MiniLM-L6-v2",
    "url": "https://chroma-onnx-models.s3.amazonaws.com/all-MiniLM-L6-v2/onnx.tar.gz",
    "archive_sha256": "913d7300ceae3b2dbc2c50d1de4baacab4be7b9380491c27fab7418616a16ec3",
    "model_file_sha256": "4f148ba8ae9c2c7fbee4af2b132db8d06c6a6545b47fc83bbb98c3d22b8393e6",
    "license": "Apache-2.0",
}


def cache_dir() -> Path:
    return Path(os.environ.get("GATEDMIND_CACHE") or ROOT / ".cache")


def minilm_dir() -> Path:
    return cache_dir() / "models" / "minilm" / "onnx"


class HashEmbedder:
    """Feature hashing of word unigrams and bigrams, L2-normalized. Offline and deterministic.

    A stand-in for a model in tests. It is not a semantic embedder.
    """

    name = "hash"

    def __init__(self, dim: int = 256):
        self.dim = dim

    def embed_query(self, text: str) -> np.ndarray:
        v = np.zeros(self.dim, dtype=np.float32)
        toks = tokenize(text)
        for f in toks + [f"{a}_{b}" for a, b in zip(toks, toks[1:], strict=False)]:
            h = int.from_bytes(hashlib.blake2b(f.encode(), digest_size=8).digest(), "little")
            v[h % self.dim] += 1.0 if (h >> 63) & 1 else -1.0
        n = np.linalg.norm(v)
        return v / n if n else v

    def embed(self, texts: list[str]) -> np.ndarray:
        return np.array([self.embed_query(t) for t in texts], dtype=np.float32).reshape(
            len(texts), self.dim
        )


class MiniLMEmbedder:
    name = "minilm"

    def __init__(self, threads: int | None = None):
        from fastembed import TextEmbedding

        path = minilm_dir()
        if not (path / "model.onnx").exists():
            raise FileNotFoundError(
                f"{path}/model.onnx missing. Run: python scripts/fetch_model.py"
            )
        self.model = TextEmbedding(
            MINILM["fastembed_name"], specific_model_path=str(path), threads=threads
        )

    def embed(self, texts: list[str]) -> np.ndarray:
        out = list(self.model.embed(texts, batch_size=32))
        return np.array(out, dtype=np.float32).reshape(len(texts), -1)

    def embed_query(self, text: str) -> np.ndarray:
        return np.asarray(next(iter(self.model.query_embed(text))), dtype=np.float32)


def get_embedder(name: str):
    if name == "hash":
        return HashEmbedder()
    if name == "minilm":
        return MiniLMEmbedder()
    raise ValueError(f"unknown embedder {name!r}")
