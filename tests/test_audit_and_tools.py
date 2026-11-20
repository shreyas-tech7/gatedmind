import json

from helpers import seed1

from gatedmind.audit import AuditLog
from gatedmind.index import sentences
from gatedmind.tools import NOT_FOUND, Tools


def _pick(index):
    for doc_id in sorted(index.titles):
        yes = [p for p in sorted(index.people) if index.doc_allowed(p, doc_id)]
        no = [p for p in sorted(index.people) if not index.doc_allowed(p, doc_id)]
        if yes and no:
            return doc_id, yes[0], no[0]


def test_tools_enforce_rules(seed1_index):
    t = Tools(seed1_index)
    doc_id, yes, no = _pick(seed1_index)
    title = seed1_index.titles[doc_id]
    hit = json.loads(t.call("search", {"identity": yes, "query": title})[0])
    assert doc_id in {r["doc_id"] for r in hit}
    miss = json.loads(t.call("search", {"identity": no, "query": title})[0])
    assert doc_id not in {r["doc_id"] for r in miss}
    assert t.call("get_doc", {"identity": no, "doc_id": doc_id}) == (NOT_FOUND, True)
    assert t.call("get_doc", {"identity": no, "doc_id": "d999"}) == (NOT_FOUND, True)
    text, err = t.call("get_doc", {"identity": yes, "doc_id": doc_id})
    assert not err and json.loads(text)["doc_id"] == doc_id


def test_who_knows_names_only_owners_of_readable_documents(seed1_index):
    t = Tools(seed1_index)
    for pid in ("p001", "p015", "p033"):
        out = json.loads(
            t.call("who_knows", {"identity": pid, "topic": "budget for project atlas"})[0]
        )
        rows = seed1_index.allowed_rows(pid)
        visible = {seed1_index.owners[seed1_index.doc_ids[r]] for r in rows.tolist()}
        assert {o["person_id"] for o in out} <= visible


def test_tools_reject_bad_input(seed1_index):
    t = Tools(seed1_index)
    assert t.call("search", {"identity": "nobody", "query": "x"}) == ("unknown identity", True)
    assert t.call("search", {"identity": "p001", "query": "x", "k": 99})[1]
    assert t.call("search", {"identity": "p001", "query": "x" * 501})[1]
    assert t.call("search", {"identity": "p001", "query": "x", "k": True})[1]
    assert t.call("drop_table", {"identity": "p001"})[1]


def test_audit_log_stores_ids_and_counts_but_no_document_text(seed1_index, tmp_path):
    """Broken case: logging the snippets or the query would copy document text into the log."""
    org, qs = seed1()
    log = tmp_path / "audit.jsonl"
    t = Tools(seed1_index, AuditLog(log))
    for q in qs:
        t.call("search", {"identity": q["asker"], "query": q["text"]})
        t.call("who_knows", {"identity": q["asker"], "topic": q["text"]})
        for d in q["gold_docs"]:
            t.call("get_doc", {"identity": q["asker"], "doc_id": d})
    raw = log.read_text()
    entries = [json.loads(line) for line in raw.splitlines()]
    assert len(entries) >= 3 * len(qs)
    assert set(entries[0]) == {
        "ts",
        "identity",
        "action",
        "mode",
        "query_sha256",
        "returned_doc_ids",
        "denied_chunks",
    }
    assert any(e["denied_chunks"] > 0 for e in entries)
    for d in org["docs"]:
        assert d["value"] not in raw
        assert d["title"] not in raw
        for s in sentences(d["text"]):
            assert s not in raw
    for q in qs:
        assert q["text"] not in raw
