# Tooling

| Tool | Source | Version | Why | Check result |
| --- | --- | --- | --- | --- |
| superpowers skills | already in the session (claude.ai account) | as installed | plans, TDD, debugging, verification | used by hand inline, to save tokens |
| ponytail, caveman, humanizer | `npx skills add ...` | none | code style, terse progress, doc pass | not installed. Earlier builds in this project had the install denied by the permission system, so the install was not retried. Their rules were applied by hand (small plain code, plain-word docs) |
| security-audit | `anthropic-skills:security-audit`, in the session's skill list | as installed | release check audit | used in the release check |
| gitleaks | `go install github.com/zricethezav/gitleaks/v8@latest` | v8.30.1 tree (go install build) | secret scan before each commit | installed, clean |
| actionlint | `go install github.com/rhysd/actionlint/cmd/actionlint@latest` | v1.7.12 | workflow lint | installed, both workflows pass |
| pip-audit | `uv tool install pip-audit` | latest on 2026-11-20 | dependency audit | installed |
| cisco-ai-mcp-scanner | `uv tool install cisco-ai-mcp-scanner` | latest on 2026-11-20 | scan the MCP tool list (yara and static) | installed, see docs/SECURITY_CHECKS.md |
| ruff | PyPI (dev extra) | at install time | lint, format, `--select S` | runs in init.sh |
| graphify, cisco-ai-skill-scanner, pre-commit | `uv tool install` | not installed | not needed: under 30 source files, no new skills installed, gitleaks runs directly | skipped |
