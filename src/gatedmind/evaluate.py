"""Run every question through every mode and score accuracy, leaks, over-blocking and latency.

Scoring uses the reference rule check in `org.can_read`, not the SQL grants, so a bug in
the index metadata shows up as a leak or an over-block.

- leak: the answer cites a document outside `may_appear`, or contains its fact value.
- accuracy: when the asker may read a gold document, the answer cites one. When the asker
  may read none, the answer cites no gold document and leaks nothing.
- over-blocking: the asker may read a gold document and a reference permission-aware search
  (same k, same retriever, rules from `org.can_read`) returns it, but the answer drops it.
"""

from __future__ import annotations

import datetime as dt
import json
import platform
from pathlib import Path

import numpy as np

from . import metrics, modes
from .index import Index
from .org import can_read


def cpu_model() -> str:
    try:
        for line in Path("/proc/cpuinfo").read_text().splitlines():
            if line.startswith("model name"):
                return line.split(":", 1)[1].strip()
    except OSError:
        pass
    return platform.processor() or "unknown"


def score_one(q: dict, res: modes.Result, values: dict[str, str], ideal_docs: set[str]) -> dict:
    may = set(q["may_appear"])
    leaked = {d for d in res.cited if d not in may}
    leaked |= {d for d, v in values.items() if d not in may and v in res.answer}
    allowed_gold = set(q["allowed_gold"])
    cited = set(res.cited)
    if allowed_gold:
        correct = bool(cited & allowed_gold)
    else:
        correct = not (cited & set(q["gold_docs"])) and not leaked
    eligible = bool(allowed_gold & ideal_docs)
    return {
        "q": q["id"],
        "leaked": sorted(leaked),
        "correct": correct,
        "overblock_eligible": eligible,
        "overblocked": eligible and not (cited & allowed_gold),
        "chunks_to_model": len(res.context_rows),
        "latency_ms": res.latency_ms,
    }


def summarize(rows: list[dict]) -> dict:
    n = len(rows)
    leaks = sum(bool(r["leaked"]) for r in rows)
    correct = sum(r["correct"] for r in rows)
    elig = [r for r in rows if r["overblock_eligible"]]
    over = sum(r["overblocked"] for r in elig)
    lat = [r["latency_ms"] for r in rows]
    p50, p95 = metrics.percentile(lat, 50), metrics.percentile(lat, 95)
    return {
        "n": n,
        "accuracy": {"k": correct, "n": n, "ci": metrics.wilson(correct, n)},
        "leak_rate": {"k": leaks, "n": n, "ci": metrics.wilson(leaks, n)},
        "overblock_rate": {"k": over, "n": len(elig), "ci": metrics.wilson(over, len(elig))},
        "leak_upper_rule_of_three": metrics.rule_of_three(n) if leaks == 0 else None,
        "chunks_to_model_mean": round(float(np.mean([r["chunks_to_model"] for r in rows])), 3),
        "latency_p50_ms": round(p50, 3),
        "latency_p95_ms": round(p95, 3),
        "latency_p50_ci": [round(x, 3) for x in metrics.bootstrap_ci(lat, 50)],
        "latency_p95_ci": [round(x, 3) for x in metrics.bootstrap_ci(lat, 95)],
    }


def run(org: dict, questions: list[dict], index: Index, retriever: str, k: int = 4) -> dict:
    people = {p["id"]: p for p in org["people"]}
    values = {d["id"]: d["value"] for d in org["docs"]}
    docs_by_id = {d["id"]: d for d in org["docs"]}
    ref_rows: dict[str, np.ndarray] = {}
    for pid, person in people.items():
        ok = {d for d, doc in docs_by_id.items() if can_read(person, doc, org["folders"])}
        ref_rows[pid] = np.array([i for i, d in enumerate(index.doc_ids) if d in ok], np.int64)
    # Warm up once so the first query does not pay for imports and caches.
    modes.run(index, questions[0]["asker"], questions[0]["text"], "none", k, retriever)
    out: dict = {"modes": {}, "details": {}}
    for mode in modes.MODES:
        rows = []
        for q in questions:
            res = modes.run(index, q["asker"], q["text"], mode, k, retriever)
            ideal = index.search(q["text"], k, rows=ref_rows[q["asker"]], retriever=retriever)
            rows.append(score_one(q, res, values, {index.doc_ids[h] for h in ideal}))
        out["modes"][mode] = summarize(rows)
        out["details"][mode] = [
            {key: r[key] for key in ("q", "leaked", "correct", "overblocked")}
            for r in rows
            if r["leaked"] or not r["correct"] or r["overblocked"]
        ]
    return out


def run_all(org, questions, indexes: dict[str, Index], k: int = 4) -> dict:
    result = {
        "seed": org["seed"],
        "date": dt.date.today().isoformat(),
        "model": "scripted fake model (gatedmind.model), no real model",
        "k": k,
        "n_questions": len(questions),
        "n_docs": len(org["docs"]),
        "n_people": len(org["people"]),
        "cpu": cpu_model(),
        "cores_used": 1,
        "python": platform.python_version(),
        "retrievers": {},
    }
    for name, index in indexes.items():
        result["retrievers"][name] = run(org, questions, index, name, k)
    return result


def save(result: dict, path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(result, indent=1, sort_keys=True) + "\n", encoding="utf-8")
