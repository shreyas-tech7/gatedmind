"""Test guard: any socket connection to a host that is not local fails the test."""

import socket
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent))

LOCAL = {"localhost", "127.0.0.1", "::1"}
_real_connect = socket.socket.connect


class NetworkBlocked(RuntimeError):
    pass


def _guarded_connect(self, address):
    host = address[0] if isinstance(address, tuple) else address
    if self.family == socket.AF_UNIX or host in LOCAL:
        return _real_connect(self, address)
    raise NetworkBlocked(f"test tried to reach {host!r}; tests must run offline")


@pytest.fixture(autouse=True)
def _no_network(monkeypatch):
    monkeypatch.setattr(socket.socket, "connect", _guarded_connect)
    yield


@pytest.fixture(scope="session")
def seed1_index(tmp_path_factory):
    from helpers import seed1

    from gatedmind.index import Index, build

    org, _ = seed1()
    path = build(org, tmp_path_factory.mktemp("ix") / "seed1.sqlite")
    return Index(path)


@pytest.fixture(scope="session")
def seed1_hash_index(tmp_path_factory):
    from helpers import seed1

    from gatedmind.embed import HashEmbedder
    from gatedmind.index import Index, build

    org, _ = seed1()
    emb = HashEmbedder()
    path = build(org, tmp_path_factory.mktemp("ixh") / "seed1-hash.sqlite", emb)
    return Index(path, emb)
