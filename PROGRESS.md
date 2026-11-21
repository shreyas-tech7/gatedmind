# Progress

Done: F01 to F18, 2026-11-20.

- F01 to F12 (seed 1 only): generator with traps, eval suite, SQLite index with grants, BM25,
  hash and MiniLM embedders, fake model, four modes, metrics, leak gate, audit log, MCP server
  with the stdio smoke test.
- F13: seed 2 final run, once, in results/final-seed2.json. Modes 1 and 2 had no leaks, so no
  seed 3 was needed.
- F14 to F16: README written from the results by script, quality bar, study-later kit.
- F17: release check in docs/RELEASE_CHECK.md and docs/SECURITY_CHECKS.md.
- F18: release candidate and hand-off. The release SHA is in CHANGELOG.md and docs/HUMAN_STEPS.md.

Next: only the human steps in docs/HUMAN_STEPS.md.

Open blockers: none that stop the brief. See BLOCKERS.md. GitHub has no `main` yet, so the pull
request waits for Shreyas.

Last `./init.sh`: all checks passed, 2026-11-20. GitHub Actions CI passed on the branch.
