# Walkthrough

A tour of every file. Short sentences, one idea each.

## The big picture

The repo makes a fake company. The company has people and documents. Each document has rules about who may read it. Someone asks a question as one of the people. The system searches the documents. One of four modes decides what the search may return. A fake model writes an answer from what it got. A scorer checks the answer for leaks.

## Source code (`src/gatedmind/`)

- `org.py` makes the fake company. It has 4 departments and 40 people. Each person has a department, a role and some projects. It writes about 300 short documents. Each document holds one fact, like a budget or a date. Each fact value is unique, so a value in an answer points to one document.
- `org.py` also holds the access rules. A rule is a list of names, called principals. `principals()` lists every name that fits a person. `can_read()` says yes when a document's list and the person's list share a name. This is the reference check. The scorer trusts it.
- `org.py` plants three traps. The twin is a restricted draft that copies an open document with a new number. The single-person note has exactly one reader. The folder trap is a file with no rules of its own, so it takes its folder's rules.
- `questions.py` writes the 200 questions. Each one asks for one fact. Each one names an asker. Each one lists the documents that the asker may see (`may_appear`). Some questions swap a word for a synonym.
- `bm25.py` is a classic word-match search. It is written with numpy, no search engine needed.
- `embed.py` turns text into vectors. The hash embedder is a fake for tests. The MiniLM embedder is a small real model that runs on a CPU through FastEmbed.
- `index.py` cuts each document into chunks of two sentences. It saves every chunk in SQLite. It also saves one grant row per chunk and principal. That is the access metadata. `allowed_rows()` asks SQL which chunks an identity may read. `search()` ranks chunks, and can limit the ranking to given rows.
- `model.py` is the fake model. It quotes the best sentence of each chunk with the document ID in brackets. Then it writes a summary line. The summary restates each fact in new words. That is how a real model leaks after redaction.
- `modes.py` holds the four modes. Pre-filter limits the search to allowed rows. Post-filter searches everything, then drops forbidden chunks. Redact lets the model see everything, then removes bad lines from the answer. None does nothing.
- `metrics.py` has the math. Wilson intervals for rates. The rule of three. Percentiles and a bootstrap for latency.
- `evaluate.py` runs every question through every mode. It scores leaks, accuracy, over-blocking and latency. It uses `org.can_read`, not the SQL grants, so an index bug shows up as a leak.
- `audit.py` writes one JSON line per tool call. It keeps the identity, the action, the returned document IDs and the denied chunk count. It keeps a hash of the query, never the text.
- `tools.py` holds the three tools: `search`, `get_doc` and `who_knows`. They always use pre-filter. `get_doc` gives the same error for a missing document and a forbidden one.
- `mcp_server.py` serves those tools over stdio with the official MCP SDK.
- `report.py` writes the README result blocks and `docs/index.html` from the results files.
- `cli.py` is the `gatedmind` command. It refuses any seed but 1 unless you pass `--final`.

## Data and results

- `data/seed1/` holds the build seed: `org.json` and `questions.json`.
- `data/seed2/` holds the held-out seed. It was made once, for the final run.
- `results/dev-seed1.json` is the build run. `results/final-seed2.json` is the final run.

## Tests (`tests/`)

- `conftest.py` blocks every network call that is not local. `test_network_guard.py` proves it.
- `test_org.py` and `test_questions.py` check the company, the traps and the questions.
- `test_index.py` checks that the SQL grants match `can_read` for every person and chunk.
- `test_model.py` and `test_modes.py` check the fake model and the four modes.
- `test_leaks.py` is the leak gate. Modes 1 and 2 must show zero leaks. Modes 3 and 4 must show some. A broken pre-filter must get caught.
- `test_audit_and_tools.py` checks the tools and that no document text reaches the audit log.
- `test_mcp_smoke.py` starts the real MCP server and calls each tool.
- `test_cli.py` checks the seed guard. `test_repo.py` checks the README and the docs.

## Scripts (`scripts/`)

- `fetch_model.py` downloads MiniLM and checks two hashes.
- `mcp_smoke.py` is the MCP smoke test with the official client.
- `check_links.py` checks every link in the docs.
- `make_social_preview.py` draws `docs/social-preview.png` with no image library.

## Project files

- `init.sh` installs, lints, checks links and runs every test.
- `PROGRESS.md`, `HANDOVER.md`, `BLOCKERS.md`, `DECISIONS.md` and `feature_list.json` are the build's memory.
- `.github/workflows/ci.yml` runs `init.sh`, the README check and the MCP smoke test.
