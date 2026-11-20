"""The leak gate. Modes 1 and 2 must show zero leaks on the full suite, or the build fails.
Modes 3 and 4 must show leaks, which proves the suite can see one."""

import pytest
from helpers import seed1

from gatedmind import evaluate


@pytest.fixture(scope="module")
def bm25_result(seed1_index):
    org, qs = seed1()
    return evaluate.run(org, qs, seed1_index, "bm25")


@pytest.mark.parametrize("mode", ["prefilter", "postfilter"])
def test_zero_leaks_bm25(bm25_result, mode):
    leaks = [d for d in bm25_result["details"][mode] if d["leaked"]]
    assert leaks == [], f"{mode} leaked: {leaks[:5]}"


@pytest.mark.parametrize("ret", ["dense", "hybrid"])
def test_zero_leaks_with_the_hash_embedder(seed1_hash_index, ret):
    org, qs = seed1()
    res = evaluate.run(org, qs, seed1_hash_index, ret)
    for mode in ("prefilter", "postfilter"):
        assert res["modes"][mode]["leak_rate"]["k"] == 0, (ret, mode)


@pytest.mark.parametrize("mode", ["redact", "none"])
def test_the_suite_detects_leaks(bm25_result, mode):
    assert bm25_result["modes"][mode]["leak_rate"]["k"] > 0


def test_the_gate_catches_a_broken_prefilter(seed1_index, monkeypatch):
    """Broken case: the SQL filter returns every chunk. The gate must report leaks."""
    import numpy as np

    org, qs = seed1()
    monkeypatch.setattr(
        type(seed1_index), "allowed_rows", lambda self, ident: np.arange(len(self.texts))
    )
    res = evaluate.run(org, qs, seed1_index, "bm25")
    assert res["modes"]["prefilter"]["leak_rate"]["k"] > 0
    assert res["modes"]["postfilter"]["leak_rate"]["k"] > 0


def test_score_counts_a_leaked_value_without_a_citation():
    from gatedmind.modes import Result

    q = {"id": "q", "may_appear": ["d1"], "allowed_gold": ["d1"], "gold_docs": ["d1"]}
    res = Result("[d1] fine.\nSummary: secret: VAL-1", ["d1"], [0], 0, 1.0)
    row = evaluate.score_one(q, res, {"d1": "OK-1", "d2": "VAL-1"}, {"d1"})
    assert row["leaked"] == ["d2"] and row["correct"]


def test_metrics_shape(bm25_result):
    s = bm25_result["modes"]["prefilter"]
    assert s["n"] == 200
    assert s["leak_upper_rule_of_three"] == pytest.approx(0.015)
    assert s["latency_p50_ms"] <= s["latency_p95_ms"]
