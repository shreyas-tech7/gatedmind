from collections import Counter

from helpers import seed1

from gatedmind import org as orgmod
from gatedmind import questions as qmod


def test_suite_size_and_mix():
    _, qs = seed1()
    assert 150 <= len(qs) <= 200
    assert Counter(q["category"] for q in qs) == qmod.MIX
    answerable = sum(bool(q["allowed_gold"]) for q in qs)
    assert 0.3 * len(qs) < answerable < 0.8 * len(qs)


def test_may_appear_matches_the_reference_rules():
    org, qs = seed1()
    people = {p["id"]: p for p in org["people"]}
    for q in qs:
        p = people[q["asker"]]
        may = {d["id"] for d in org["docs"] if orgmod.can_read(p, d, org["folders"])}
        assert set(q["may_appear"]) == may
        assert set(q["allowed_gold"]) == set(q["gold_docs"]) & may


def test_committed_questions_match_the_generator():
    org, qs = seed1()
    assert qs == qmod.make_questions(org)


def test_twin_questions_have_a_forbidden_twin():
    _, qs = seed1()
    hard = [q for q in qs if q["category"] == "twin" and q["allowed_gold"]]
    assert any(set(q["gold_docs"]) - set(q["may_appear"]) for q in hard)
