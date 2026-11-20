# Security checks

Run on 2026-11-20 on branch `claude/build-gatedmind`. This is a benchmark, not a security product. The checks look for mistakes in this code. They do not prove that the access rules are safe for real data.

## Tool scans

| Check | Command | Result |
| --- | --- | --- |
| Secrets in history | `gitleaks git -v .` | no leaks found |
| Secrets in the working tree | `gitleaks dir .` | no leaks found |
| Dependency advisories | `pip-audit -r <frozen requirements> --no-deps --disable-pip` | no known vulnerabilities in 56 packages |
| Security lint | `ruff check --select S src scripts tests` | all checks passed after one fix |
| Workflow lint | `actionlint` | no findings |
| Links | `python scripts/check_links.py` | relative links pass, 3 outside links not checked |
| MCP tool scan | `mcp-scanner --analyzers yara static --tools <tools.json>` | 3 tools scanned, 3 safe, 0 findings |

The ruff fix: `tests/test_repo.py` runs our own link script with a fixed argument list. It now carries a `noqa: S603` comment with that reason. Two `S608` and two `S311` comments were already in place. The SQL builds only `?` placeholders, and the random numbers make synthetic data, not keys.

The MCP scan used the tool list from `gatedmind tools-json`, wrapped as `{"tools": [...]}`. The scanner printed a default "Scan Target" web address in its summary, but a static scan reads only the local file and sends nothing.

## Code audit

A manual audit followed the security-audit skill (STRIDE threat model, then a trace from each input to each sink). It looked at the four modes, the identity check in the MCP tools, the index and the audit log.

| Finding | Severity | Status |
| --- | --- | --- |
| The MCP `identity` argument is a claim, not a sign-in. Any caller can claim any person. | High in a real system | Accepted and stated in the README, the tool schema and `docs/INTERVIEW_QA.md`. Real use needs identity from a verified session. |
| An unexpected exception inside a tool could reach the MCP client with internal details. | Medium | Fixed. `Tools.call` now answers `internal error` for any non-tool error. Test: `test_internal_errors_do_not_leak_details`. |
| The audit log file used the default file mode, so other local users might read which person asked for which document IDs. | Low | Fixed. The log is created with mode 0600. Test: `test_audit_log_is_owner_only`. |
| The index path went into an SQLite URI as raw text, so a `?` in a path could change the open mode. | Low | Fixed. The path is now turned into a proper file URI before `?mode=ro` is added. |
| BM25 word statistics are computed over every chunk, so result order can depend on words in forbidden documents. | Low | Accepted. No scores are returned. Logged as a limit and as interview question 15. |
| The query is stored as a plain SHA-256 hash. A short, guessable question can be confirmed by hashing guesses. | Low | Accepted for a benchmark. A keyed hash (HMAC with a secret) is the fix for real use. |
| Tool results carry document text to the calling agent. A document could hold a prompt injection aimed at that agent. | Low | Accepted. Only allowed text is returned, and the calling agent must treat it as data. |
| Mode 3 (redact after generation) leaks by design. | By design | It is the control that shows why filtering must come first. It is never used by the MCP tools. |

Checked and found sound:

- Modes 1 and 2 never put a forbidden chunk in the model's context. The leak gate in `tests/test_leaks.py` fails the build if they do, and a mutation test proves the gate can fail.
- An unknown identity raises before any search in every mode, and the tools answer `unknown identity`.
- SQL uses only `?` placeholders, and the index opens read-only.
- A document with no rules and no folder rules stops the index build, so nothing becomes public by accident.
- `get_doc` gives the same answer for a missing and a forbidden document.
- The audit log stores IDs, counts and a query hash. A test runs every question through every tool and finds no document text or question text in the log.
- The MCP server speaks only over stdio and opens no network port.
