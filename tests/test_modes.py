import pytest
from helpers import seed1

from gatedmind import modes


def _twin_case(index):
    """A question whose gold has a restricted twin the asker may not read."""
    _, qs = seed1()
    for q in qs:
        forbidden = set(q["gold_docs"]) - set(q["may_appear"])
        if q["category"] == "twin" and q["allowed_gold"] and forbidden:
            return q, forbidden
    raise AssertionError("no twin question")


def test_control_leaks_the_twin_and_filters_do_not(seed1_index):
    org, _ = seed1()
    q, forbidden = _twin_case(seed1_index)
    values = {d["id"]: d["value"] for d in org["docs"]}
    none = modes.run(seed1_index, q["asker"], q["text"], "none")
    assert forbidden & set(none.cited)
    for m in ("prefilter", "postfilter"):
        r = modes.run(seed1_index, q["asker"], q["text"], m)
        assert not forbidden & set(r.cited)
        assert not any(values[d] in r.answer for d in forbidden)


def test_redaction_drops_cited_lines_but_the_summary_still_leaks(seed1_index):
    """The point of mode 3: text the model has read can come back in other words."""
    org, _ = seed1()
    q, forbidden = _twin_case(seed1_index)
    values = {d["id"]: d["value"] for d in org["docs"]}
    r = modes.run(seed1_index, q["asker"], q["text"], "redact")
    assert not forbidden & set(r.cited)
    assert any(values[d] in r.answer for d in forbidden)


def test_redact_removes_forbidden_lines():
    ans = "[d001] Open text.\n[d002] Secret text.\nSummary: x: 1"
    out = modes.redact(ans, {"d002"}, ["Secret text."])
    assert out == "[d001] Open text.\nSummary: x: 1"
    assert (
        modes.redact("[d002] Secret text.", {"d002"}, [])
        == "I found nothing you are allowed to read about this."
    )


def test_postfilter_can_starve_the_context(seed1_index):
    _, qs = seed1()
    sizes = [
        len(modes.run(seed1_index, q["asker"], q["text"], "postfilter").context_rows)
        for q in qs
        if q["category"] == "cluster"
    ]
    assert min(sizes) < 4
    pre = [
        len(modes.run(seed1_index, q["asker"], q["text"], "prefilter").context_rows)
        for q in qs
        if q["category"] == "cluster"
    ]
    assert min(pre) == 4


@pytest.mark.parametrize("mode", modes.MODES)
def test_unknown_identity_is_refused_in_every_mode(seed1_index, mode):
    with pytest.raises(KeyError):
        modes.run(seed1_index, "nobody", "budget", mode)


def test_unknown_mode(seed1_index):
    with pytest.raises(ValueError):
        modes.run(seed1_index, "p001", "budget", "trust-me")
