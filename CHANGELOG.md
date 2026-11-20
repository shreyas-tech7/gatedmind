# Changelog

## v0.1.0-rc1 (release candidate, 2026-11-20)

Release commit: `RELEASE_SHA`


- Synthetic org generator with three traps: a restricted twin, a single-person note and a folder that passes its rules to its files.
- SQLite index with access rules on every chunk, BM25, MiniLM through FastEmbed and a hash embedder for tests.
- Four enforcement modes: pre-filter, post-filter, redact after and none.
- Scripted fake model that quotes its context and paraphrases facts in a summary line.
- Eval suite of 200 questions per seed with accuracy, leak rate, over-blocking and latency.
- Leak gate test that fails the build on any leak in modes 1 or 2.
- Audit log with IDs and counts only, and a test that no document text reaches it.
- MCP server with `search`, `get_doc` and `who_knows`, and a stdio smoke test with the official client.
- Final numbers from held-out seed 2 in `results/final-seed2.json`, with seed 1 numbers in `results/dev-seed1.json`. The README tables come from these files by script.
- Security fixes from the release audit: tool errors fail closed without internal details, the audit log file is owner-only, and the index path is escaped as a file URI.
- Study-later kit and hand-off: walkthrough, interview questions, security checks, human steps and a Cowork prompt.
