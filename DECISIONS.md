# Decisions

One line per choice: what was picked, what else was weighed, and why.

- Name: `gatedmind`. On 2026-11-20 `https://pypi.org/pypi/gatedmind/json` and `https://registry.npmjs.org/gatedmind` both answered 404, and a web search for "gatedmind" github showed no well-known project. Backups `orgbrain` and `orgmind` were not needed. The repo name already matches.
- Branch: `claude/build-gatedmind`, as the coordinator brief asks. GitHub had no `main`, so the branch starts from a fresh first commit. No `main` was created.
- Access rule format: a list of principal strings (`all`, `dept:X`, `role:X`, `deptrole:X/Y`, `project:X`, `user:X`). Weighed a rule language like OpenFGA tuples. Strings make the SQL filter one `IN (...)` query and keep the reference check in `org.can_read` to three lines.
- Folder rules: a file with no rules of its own takes its folder's rules. A file with its own rules uses only its own. Weighed a union of both. Replacement is easier to reason about and makes the single-person trap possible inside a wider folder.
- Folder rules are resolved when the index is built and stored on every chunk. Weighed resolving at query time. Build-time resolution matches "each chunk stores its access metadata" and keeps the query to one table.
- Fact values have a fixed width per kind (for example 10.0 to 49.9 percent), so no value is a substring of another. Found when "4.5 percent" would have matched inside "14.5 percent" and counted as a false leak.
- Leak = the answer cites a document outside `may_appear` or contains its fact value. Weighed fuzzy text overlap. Exact IDs and unique values make every leak mechanical and easy to audit.
- The fake model writes a summary line that restates facts in new words. Without it, exact-match redaction (mode 3) would look perfect. Real models paraphrase, and the dev.to write-up in Related work makes the same point.
- Accuracy is scored by documents, not text, as the brief says. For a question the asker may not answer, "correct" means no gold document and no leak in the answer.
- Over-blocking = the asker may read a gold document and a reference permission-aware search (rules from `org.can_read`, same k and retriever) returns it, but the answer does not cite it. By this definition a correct pre-filter scores 0, so the number checks that mode 1's SQL agrees with the reference rules. Mode 4's number is crowding by forbidden chunks, not blocking. The README says so.
- k = 4 chunks to the model. Small enough that crowding by forbidden chunks shows up in mode 2, large enough to answer every question.
- Pre-filter with BM25 scores the allowed rows only, but the IDF comes from the whole corpus. Weighed a per-identity BM25. A per-identity index is the stronger design but costs one index per access set. Logged as a limit.
- Questions sometimes swap a word for a synonym ("budget" to "spending plan"), so retrieval is not a pure word match. The subjects stay distinctive, so retrieval is still easy. The README says the benchmark measures leaks, not retrieval quality.
- Dense model: all-MiniLM-L6-v2 ONNX from the Chroma S3 archive, pinned by sha256. Hugging Face answered with a blocked tunnel, and the brief prefers a small CPU model. The same route worked for cpu-rag-lab.
- MCP SDK: `mcp==2.3.0` (latest on PyPI on 2026-11-20) with the low-level `Server`. In 2.x `FastMCP` was renamed, and the low-level server needs no decorators.
- MCP tools always use mode 1. `get_doc` gives the same error for a missing and a forbidden document, so the tool does not confirm that a secret document exists.
- Audit log stores the SHA-256 of the query, not the query. A question can quote a document, and the brief says the log stores IDs, not text.
- Seed guard: the CLI refuses any seed other than 1 unless `--final` is passed, so building and tuning cannot touch seed 2 by accident.
- Skills: ponytail, caveman, humanizer and the security-audit skill were applied by hand or from the session's own skill list. See docs/TOOLING.md.
