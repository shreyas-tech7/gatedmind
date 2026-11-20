"""Download the all-MiniLM-L6-v2 ONNX export into .cache/ and check both hashes.

Source: the archive that chroma-core/chroma pins by sha256. Hugging Face is not needed.
"""

from __future__ import annotations

import hashlib
import sys
import tarfile
import urllib.request
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from gatedmind.embed import MINILM, minilm_dir  # noqa: E402


def sha(b: bytes) -> str:
    return hashlib.sha256(b).hexdigest()


def main() -> int:
    model = minilm_dir() / "model.onnx"
    if not model.exists():
        with urllib.request.urlopen(MINILM["url"], timeout=120) as r:  # noqa: S310 (fixed https URL)
            body = r.read()
        if sha(body) != MINILM["archive_sha256"]:
            raise SystemExit(f"archive hash mismatch: {sha(body)}")
        dest = minilm_dir().parent
        dest.mkdir(parents=True, exist_ok=True)
        tgz = dest / "archive.tar.gz"
        tgz.write_bytes(body)
        with tarfile.open(tgz) as t:
            t.extractall(dest, filter="data")
    got = sha(model.read_bytes())
    if got != MINILM["model_file_sha256"]:
        raise SystemExit(f"model.onnx hash mismatch: {got}")
    print("model ok", got[:12])
    return 0


if __name__ == "__main__":
    sys.exit(main())
