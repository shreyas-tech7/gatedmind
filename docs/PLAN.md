# gatedmind plan

Goal: answer questions from synthetic company documents with four permission modes, and
publish the leak rate of each. The brief in docs/build/BUILD_PROMPT.md is the spec.

Architecture: generate org and questions, build a SQLite index with per-chunk grants,
run each question through a mode, answer with a scripted fake model, then log and score.

Tasks (each one test first, then code, then `./init.sh`):

1. `org.py`: departments, 40 people, projects, folders, about 300 documents, three traps. Test: `tests/test_org.py`.
2. `questions.py`: 200 questions with asker, gold docs and `may_appear`. Test: `tests/test_questions.py`.
3. `index.py`: two-sentence chunks, tables people, docs, chunks, grants. BM25. Test: `tests/test_index.py`.
4. `embed.py`: hash embedder, MiniLM through FastEmbed, dense and hybrid search. Test: dense tests in `tests/test_index.py`.
5. `model.py`: quotes, citations, summary line. Test: `tests/test_model.py`.
6. `modes.py`: mode 4, then 1, 2 and 3. Test: `tests/test_modes.py`.
7. `evaluate.py`, `metrics.py`: accuracy, leak, over-block, latency with intervals. Test: `tests/test_metrics.py`.
8. Leak gate. Test: `tests/test_leaks.py`, with a broken pre-filter that must be caught.
9. `audit.py`. Test: no document text or query text in the log.
10. `tools.py`, `mcp_server.py`, `scripts/mcp_smoke.py`. Test: `tests/test_mcp_smoke.py`.
11. Seed 2 final run, README from `report.py`, study-later kit, release check, hand-off.

Assumptions (also in DECISIONS.md): access rules are principal lists, own rules replace
folder rules, accuracy is scored by documents, k = 4, the fake model paraphrases in a
summary line, and over-blocking is measured against a reference permission-aware search.
