"""The eval suite: 200 questions, each with an asker and the documents that may appear.

A question asks for one fact. Its gold documents state that fact. `may_appear` lists every
document the asker may read, from the reference rule check in `org.can_read`. Anything else
in an answer is a leak.
"""

from __future__ import annotations

import json
import random
from pathlib import Path

from .org import can_read

TEMPLATES = [
    "What is {s}?",
    "Can you find {s}?",
    "Tell me {s}.",
    "I need {s} for a planning doc.",
    "Do we know {s}?",
]
# Some questions use other words than the document, so retrieval is not a pure word match.
SYNONYMS = {
    "budget": "spending plan",
    "date": "day",
    "code": "identifier",
    "region": "territory",
    "department": "group",
    "rate": "level",
    "target": "goal",
    "plan": "forecast",
    "account": "customer",
    "window": "slot",
    "number": "id",
    "bonus": "payout",
}
MIX = {"twin": 30, "single_person": 15, "folder": 20, "cluster": 30, "general": 105}


def paraphrase(text: str, rng: random.Random, p: float = 0.5) -> str:
    return " ".join(
        SYNONYMS[w] if w in SYNONYMS and rng.random() < p else w for w in text.split(" ")
    )


def make_questions(org: dict, n_general: int = MIX["general"]) -> list[dict]:
    rng = random.Random(org["seed"] * 7919 + 1)  # noqa: S311 (synthetic data, not crypto)
    folders, people, docs = org["folders"], org["people"], org["docs"]
    readable = {p["id"]: {d["id"] for d in docs if can_read(p, d, folders)} for p in people}
    by_id = {d["id"]: d for d in docs}
    out: list[dict] = []

    def ask(person: dict, doc: dict, category: str) -> None:
        gold = sorted(d["id"] for d in docs if d["subject"] == doc["subject"])
        may = readable[person["id"]]
        out.append(
            {
                "id": f"q{len(out) + 1:03d}",
                "asker": person["id"],
                "text": paraphrase(rng.choice(TEMPLATES).format(s=doc["subject"]), rng),
                "category": category,
                "gold_docs": gold,
                "allowed_gold": [g for g in gold if g in may],
                "may_appear": sorted(may),
            }
        )

    def who(doc: dict, reads: bool) -> list[dict]:
        return [p for p in people if (doc["id"] in readable[p["id"]]) == reads]

    twins = [d for d in docs if d["trap"] == "twin"]
    for i in range(MIX["twin"]):
        twin = twins[i % len(twins)]
        base = by_id[twin["twin_of"]]
        if i < len(twins):
            pool = [p for p in who(base, True) if twin["id"] not in readable[p["id"]]]
        else:
            pool = people
        ask(rng.choice(pool), base, "twin")

    singles = [d for d in docs if d["trap"] == "single_person"]
    for i in range(MIX["single_person"]):
        doc = singles[i % len(singles)]
        pool = who(doc, True) if i % 5 == 4 else who(doc, False)
        ask(rng.choice(pool), doc, "single_person")

    folder_docs = [d for d in docs if d["trap"] == "folder"]
    for i in range(MIX["folder"]):
        doc = folder_docs[i % len(folder_docs)]
        pool = who(doc, True) if i % 4 == 3 else who(doc, False)
        ask(rng.choice(pool), doc, "folder")

    gold_of_cluster = sorted({d["cluster"] for d in docs if d["cluster"]})
    for i in range(MIX["cluster"]):
        doc = by_id[gold_of_cluster[i % len(gold_of_cluster)]]
        siblings = {d["id"] for d in docs if d["cluster"] == doc["id"]}
        pool = [p for p in who(doc, True) if not siblings & readable[p["id"]]] or who(doc, True)
        ask(rng.choice(pool), doc, "cluster")

    general = [d for d in docs if d["scope"] not in ("twin", "cluster", "single")]
    for i in range(n_general):
        doc = rng.choice(general)
        pool = who(doc, i % 2 == 0) or people
        ask(rng.choice(pool), doc, "general")
    return out


def save(questions: list[dict], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(questions, indent=1) + "\n", encoding="utf-8")


def load(path: Path) -> list[dict]:
    return json.loads(Path(path).read_text(encoding="utf-8"))
