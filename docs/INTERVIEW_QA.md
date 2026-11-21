# Interview questions and answers

Each answer points to the code (file and function) and to the results (file and number). The numbers come from `results/final-seed2.json` (seed 2, 200 questions, 2026-11-20, scripted fake model) unless a line says seed 1.

## 1. Why must filtering happen before generation?

A model cannot un-read text. Once a forbidden chunk is in the prompt, the model can quote it or restate it. Mode 3 in `src/gatedmind/modes.py` (`run` with `mode="redact"`) shows this. It removes every line that cites a forbidden document and every forbidden sentence quoted word for word. It still leaks on 127 of 200 questions with BM25, because the summary line from `src/gatedmind/model.py` (`answer`) restates the fact in new words. Modes 1 and 2 never put forbidden text in the prompt and leak on 0 of 200.

## 2. Why does pre-filtering keep the top results full, while post-filtering can starve them?

Pre-filter (`modes.run` with `mode="prefilter"`) asks SQL for the allowed rows first (`Index.allowed_rows`) and ranks only those. So the top 4 are always the best 4 allowed chunks. Post-filter ranks everything, takes the top 4, then drops the forbidden ones. When forbidden chunks crowd the top, few are left. In the final run the model got 3.89 chunks on average with pre-filter and 1.47 with post-filter (BM25). Post-filter missed an allowed answer on 25 of 126 eligible questions (19.8%). Pre-filter missed 0.

## 3. What does the rule of three say about zero leaks?

If you see 0 events in n tries, the 95% upper bound on the true rate is about 3/n. Modes 1 and 2 had 0 leaks in 200 questions, so the true rate could still be up to about 3/200 = 1.5%. The Wilson upper bound is 1.9%. Zero leaks is evidence, not proof. See `metrics.rule_of_three` and `metrics.wilson` in `src/gatedmind/metrics.py`.

## 4. What does a test token not protect?

The MCP tools in `src/gatedmind/tools.py` take an `identity` argument such as `p007`. The server trusts it. Anyone who can call the server can claim to be the CEO. A test token proves that the rules are applied correctly for a given identity. It does not prove who is calling. A real system takes the identity from a verified sign-in, outside the model's reach, so a prompt injection cannot change it.

## 5. How do you detect a leak without a real model?

Every fact value in `src/gatedmind/org.py` is unique and fixed-width (`_Values.make`), so a value in an answer points to exactly one document. `evaluate.score_one` counts a leak when the answer cites a document outside the asker's `may_appear` list, or contains the fact value of such a document. No judging of text is needed.

## 6. How do you know the scorer is not just trusting your own SQL?

The scorer uses `org.can_read`, a three-line reference check written apart from the SQL. `tests/test_index.py::test_sql_grants_match_reference_rules_for_every_person` checks that both agree for all 40 people and every chunk. `tests/test_leaks.py::test_the_gate_catches_a_broken_prefilter` replaces the SQL filter with "allow everything" and checks that the gate reports leaks.

## 7. What are the three traps and why do they matter?

The twin is a restricted draft that copies an open document with a new number (`generate`, trap 1). The single-person note has one reader (trap 2). The folder trap is a file with no rules of its own that takes its folder's rules. An indexer that reads "no rules" as "public" leaks every such file. `tests/test_org.py` checks each trap.

## 8. Why store the access rules on every chunk?

The rules are resolved when the index is built (`index.build`) and stored as one grant row per chunk and principal. A query then needs one `IN (...)` lookup on an indexed column. It also means a chunk can never reach a search without its rules.

## 9. Why does mode 3 also over-block?

Exact-match redaction removes any line that quotes a forbidden sentence. A twin copies most sentences of its open document, so an allowed line can match a forbidden one word for word and get removed. `docs/DEMO.md` shows this for p004 and the ember code freeze. With hybrid search on seed 2, mode 3 over-blocked 19 of 126 eligible questions, against 16 for post-filter.

## 10. What goes into the audit log?

`AuditLog.write` in `src/gatedmind/audit.py` stores the time, the identity, the action, the mode, a SHA-256 hash of the query, the returned document IDs and the denied chunk count. It stores no document text and no query text. `tests/test_audit_and_tools.py::test_audit_log_stores_ids_and_counts_but_no_document_text` runs every question through every tool and checks that no title, sentence, fact value or question text reaches the log.

## 11. Why does `get_doc` give the same error for a missing and a forbidden document?

If it said "forbidden", a caller could learn that a secret document exists by trying IDs. `Tools.get_doc` returns `document not found or not allowed` in both cases.

## 12. How did you keep yourself from tuning on the test set?

The CLI refuses any seed but 1 unless `--final` is passed (`cli.guard_seed`, tested in `tests/test_cli.py`). Seed 2 was generated and scored once, after every other feature passed. Seed 1 results are in `results/dev-seed1.json` for comparison.

## 13. Why is mode 1 accuracy 100%?

Each synthetic question names its subject, such as "the Q3 2027 budget for project atlas". Word match finds it almost every time. The benchmark measures leaks, not retrieval quality. Harder, human-written questions are a proposal in `docs/PROPOSALS.md`.

## 14. What does enforcement cost in speed?

Pre-filter adds one SQL query per question. With BM25 the median was 0.22 ms with pre-filter and 0.10 ms with no enforcement, on one core of an Intel Xeon at 2.10GHz. With hybrid search the embedding dominates: 2.65 ms median for pre-filter.

## 15. What would you change for production?

Take identity from real sign-in. Keep a rule service (for example OpenFGA) as the source of truth. Re-index or update grants when rules change. Use a per-access-set index or a vector store with native filters, so word statistics do not cross access lines. Run far more queries, with real users, and get an outside review before claiming any leak rate.
