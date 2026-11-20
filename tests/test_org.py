from collections import Counter

from helpers import seed1

from gatedmind import org as orgmod


def test_generator_is_deterministic_and_seeded():
    assert orgmod.generate(1) == orgmod.generate(1)
    assert orgmod.generate(7)["docs"] != orgmod.generate(1)["docs"]


def test_committed_seed1_matches_the_generator():
    """Broken case: someone edits data/seed1 by hand, so results no longer follow from the code."""
    org, _ = seed1()
    assert org == orgmod.generate(1)


def test_org_shape():
    org, _ = seed1()
    assert sorted({p["dept"] for p in org["people"]}) == sorted(orgmod.DEPARTMENTS)
    assert len(org["people"]) == 40
    assert 280 <= len(org["docs"]) <= 320
    assert Counter(p["role"] for p in org["people"]) == {"staff": 28, "manager": 8, "director": 4}
    scopes = {d["scope"] for d in org["docs"]}
    assert {"public", "dept", "project", "single", "twin", "cluster"} <= scopes


def test_fact_values_are_unique():
    org, _ = seed1()
    values = [d["value"] for d in org["docs"]]
    assert len(values) == len(set(values))
    for d in org["docs"]:
        assert sum(d["value"] in o["text"] for o in org["docs"]) == 1


def test_trap_twin_reads_almost_like_an_open_document():
    org, _ = seed1()
    by_id = {d["id"]: d for d in org["docs"]}
    twins = [d for d in org["docs"] if d["trap"] == "twin"]
    assert len(twins) >= 10
    for t in twins:
        base = by_id[t["twin_of"]]
        assert t["subject"] == base["subject"]
        assert t["text"].replace(t["value"], base["value"]).startswith(base["text"])
        readers = [p for p in org["people"] if orgmod.can_read(p, base, org["folders"])]
        assert any(not orgmod.can_read(p, t, org["folders"]) for p in readers)


def test_trap_single_person_document():
    org, _ = seed1()
    singles = [d for d in org["docs"] if d["trap"] == "single_person"]
    assert len(singles) >= 10
    for d in singles:
        readers = [p for p in org["people"] if orgmod.can_read(p, d, org["folders"])]
        assert len(readers) == 1 and d["grants"] == [f"user:{readers[0]['id']}"]


def test_trap_folder_passes_rules_to_files():
    """Broken case: an indexer that treats a file with no rules of its own as public."""
    org, _ = seed1()
    files = [d for d in org["docs"] if d["trap"] == "folder"]
    assert len(files) >= 5
    for d in files:
        assert d["grants"] == []
        assert "all" not in org["folders"][d["folder"]]
        readers = [p for p in org["people"] if orgmod.can_read(p, d, org["folders"])]
        assert 0 < len(readers) < len(org["people"])


def test_own_rules_replace_folder_rules():
    folders = {"f": ["dept:sales"]}
    sales = {"id": "p1", "dept": "sales", "role": "staff", "projects": []}
    doc = {"folder": "f", "grants": ["user:p2"]}
    assert not orgmod.can_read(sales, doc, folders)
    assert orgmod.can_read(sales, {"folder": "f", "grants": []}, folders)
