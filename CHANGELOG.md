# Changelog

## v0.1.0-rc1 (unreleased)

- Synthetic org generator with three traps: a restricted twin, a single-person note and a folder that passes its rules to its files.
- SQLite index with access rules on every chunk, BM25, MiniLM through FastEmbed and a hash embedder for tests.
- Four enforcement modes: pre-filter, post-filter, redact after and none.
- Scripted fake model that quotes its context and paraphrases facts in a summary line.
- Eval suite of 200 questions per seed with accuracy, leak rate, over-blocking and latency.
- Leak gate test that fails the build on any leak in modes 1 or 2.
- Audit log with IDs and counts only, and a test that no document text reaches it.
- MCP server with `search`, `get_doc` and `who_knows`, and a stdio smoke test with the official client.
