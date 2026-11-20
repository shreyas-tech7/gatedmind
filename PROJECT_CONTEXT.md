# Project context: gatedmind

What it is: a permission-aware RAG demo. It answers questions from synthetic company documents and
measures how often each of four enforcement modes leaks a document the asker may not read.
It is a demo, not a security product. Identity is a test token, not authentication.

Status: see PROGRESS.md and feature_list.json.

Stack: Python 3.11+, SQLite, BM25 (numpy), FastEmbed with all-MiniLM-L6-v2 (optional extra `dense`),
a hash embedder for tests, the official MCP Python SDK (`mcp==2.3.0`), pytest, ruff.

Commands:

- `./init.sh`: venv, install, lint, link check, all tests offline.
- `gatedmind generate --seed 1`: write data/seed1/org.json and questions.json.
- `gatedmind ask --as p001 --mode prefilter "question"`: one question.
- `gatedmind eval --seed 1 --retrievers bm25,hybrid --out results/dev-seed1.json`: the suite.
- `gatedmind serve --seed 1 --audit logs/audit.jsonl`: MCP server over stdio.
- `python scripts/mcp_smoke.py`: MCP smoke test with the official client.
- `gatedmind readme [--check]`: write README result blocks and docs/index.html from results/.
- `python scripts/fetch_model.py`: download and hash-check the MiniLM ONNX files into .cache/.

Layout:

- `src/gatedmind/org.py`: synthetic org, access rules, reference `can_read`.
- `src/gatedmind/questions.py`: the 200-question eval suite.
- `src/gatedmind/index.py`: chunking and the SQLite index with per-chunk grants, search.
- `src/gatedmind/embed.py`, `bm25.py`: retrieval parts.
- `src/gatedmind/model.py`: the scripted fake model.
- `src/gatedmind/modes.py`: the four enforcement modes.
- `src/gatedmind/evaluate.py`, `metrics.py`: scoring.
- `src/gatedmind/audit.py`, `tools.py`, `mcp_server.py`: audit log and MCP tools.
- `src/gatedmind/report.py`: README and results page writer.
- `tests/`: offline tests, `tests/test_leaks.py` is the leak gate.

Rules:

- Seed 1 for building. Seed 2 is held out for the final numbers (`--final`).
- Never change tests or answer keys to make code pass. Fix the code.
- A leak in mode 1 or 2 fails the build. Fix the enforcement code, never the test.
- No network in tests. No keys. No real model.

Skills that fit: superpowers test-driven-development, systematic-debugging, verification-before-completion.

Do not read: `.venv/`, `.cache/`, `data/seed*/` in full (large JSON), `docs/build/BUILD_PROMPT.md` unless resuming.
