import numpy as np
import pytest
from helpers import seed1

from gatedmind import org as orgmod
from gatedmind.index import build, chunk


def test_chunk_two_sentences():
    assert chunk("A one. B two. C three.") == ["A one. B two.", "C three."]


def test_sql_grants_match_reference_rules_for_every_person(seed1_index):
    """Broken case: the index drops folder rules, so folder files lose their limits."""
    org, _ = seed1()
    docs = {d["id"]: d for d in org["docs"]}
    for p in org["people"]:
        rows = set(seed1_index.allowed_rows(p["id"]).tolist())
        expect = {
            i
            for i, d in enumerate(seed1_index.doc_ids)
            if orgmod.can_read(p, docs[d], org["folders"])
        }
        assert rows == expect, p["id"]


def test_every_chunk_has_access_metadata(seed1_index):
    n = seed1_index.con.execute(
        "SELECT COUNT(*) FROM chunks WHERE id NOT IN (SELECT chunk_id FROM grants)"
    ).fetchone()[0]
    assert n == 0


def test_build_refuses_a_document_without_rules(tmp_path):
    org = {
        "seed": 0,
        "people": [],
        "folders": {"f": []},
        "docs": [
            {"id": "d1", "title": "t", "folder": "f", "owner": "p1", "grants": [], "text": "A."}
        ],
    }
    with pytest.raises(ValueError):
        build(org, tmp_path / "x.sqlite")


def test_bm25_finds_the_document_and_respects_rows(seed1_index):
    org, _ = seed1()
    doc = org["docs"][0]
    hits = seed1_index.search(doc["subject"], 3)
    assert seed1_index.doc_ids[hits[0]] == doc["id"]
    others = np.array([i for i, d in enumerate(seed1_index.doc_ids) if d != doc["id"]])
    assert doc["id"] not in {
        seed1_index.doc_ids[h] for h in seed1_index.search(doc["subject"], 5, rows=others)
    }


def test_dense_and_hybrid_with_the_hash_embedder(seed1_hash_index):
    org, _ = seed1()
    doc = org["docs"][3]
    for ret in ("dense", "hybrid"):
        hits = seed1_hash_index.search(doc["subject"], 4, retriever=ret)
        assert doc["id"] in {seed1_hash_index.doc_ids[h] for h in hits}


def test_unknown_identity_raises(seed1_index):
    with pytest.raises(KeyError):
        seed1_index.allowed_rows("p999")
