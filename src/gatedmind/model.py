"""A scripted fake model that quotes its context. No real model runs anywhere in this repo.

For each context chunk it quotes the sentence that shares the most words with the question,
with the chunk's document ID in brackets. Then it writes a summary line that restates every
fact sentence in its context ("The X is Y." becomes "X: Y"). The summary is a paraphrase,
like a real model would write, so exact-match redaction cannot catch it.
"""

from __future__ import annotations

import re

from .bm25 import tokenize
from .index import sentences

FACT = re.compile(r"^The (.+) is (.+)\.$")
CITE = re.compile(r"\[(d\d{3,})\]")
NOTHING = "I found nothing you are allowed to read about this."


def answer(question: str, contexts: list[tuple[str, str]]) -> str:
    """contexts: (doc_id, chunk text) pairs, best first."""
    q = set(tokenize(question))
    lines, facts = [], []
    for doc_id, text in contexts:
        sents = sentences(text)
        best = max(sents, key=lambda s: (len(q & set(tokenize(s))), bool(FACT.match(s))))
        lines.append(f"[{doc_id}] {best}")
        facts += [f"{m[1]}: {m[2]}" for s in sents if (m := FACT.match(s))]
    if not lines:
        return NOTHING
    if facts:
        lines.append("Summary: " + "; ".join(facts))
    return "\n".join(lines)


def cited(text: str) -> list[str]:
    """Document IDs cited in an answer, in order, without repeats."""
    return list(dict.fromkeys(CITE.findall(text)))
