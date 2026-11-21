# Release check

Run on 2026-11-20 on branch `claude/build-gatedmind`, before the v0.1.0-rc1 release commit. Each step follows section 11 of the build brief.

| Step | How it ran | Result |
| --- | --- | --- |
| 1. Review of the branch diff | By hand, in the ponytail style, because the review tool could not be installed here | Hand-typed counts removed from README prose. No other must-fix items. |
| 2. Security audit | The security-audit skill on the modes, the MCP identity check, the index and the audit log | Three fixes and four accepted risks. Details in `docs/SECURITY_CHECKS.md`. |
| 3. Scans | `gitleaks`, `pip-audit`, `ruff check --select S`, `actionlint`, `scripts/check_links.py` | All clean. Details in `docs/SECURITY_CHECKS.md`. |
| 4. Humanizer | By hand on `README.md` and `docs/*.md`, because the humanizer skill could not be installed here | Plain words kept. The writing-rules test passes on every doc. |
| 5. Outside check | One subagent that did not write the code cloned the repo, ran `./init.sh` and checked each Done-means item | Items 1 to 7 passed with its own evidence, including an offline test run with the network cut and two mutations that each made the leak gate fail. Item 8 was open only on the release SHA, which this commit flow records. It also noted that the leak gate tests the hybrid path with the hash embedder, not MiniLM, because MiniLM needs a model download. That is logged in `BLOCKERS.md`. |
| 6. Clean state | `git status` and the `passes` flags in `feature_list.json` | Clean after the release commit. Every flag matches a passing check. |

GitHub Actions ran the CI workflow on each push to the branch and passed.
