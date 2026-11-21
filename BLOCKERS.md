# Blockers

| What failed | Exact error | What I did instead | Manual step |
| --- | --- | --- | --- |
| Hugging Face for FastEmbed models | `curl https://huggingface.co` gave `000` (proxy CONNECT refused) on 2026-11-20 | Loaded all-MiniLM-L6-v2 from the Chroma ONNX archive on S3, checked by sha256 | None |
| Record mode with a real model | No key variable set. `api.groq.com` and `openrouter.ai` gave `000` (proxy CONNECT refused) | Not needed by the brief. The scripted fake model is the only model. The README says so | Optional: none |
| `gh` PR, tag push, repo settings | The proxy refuses GraphQL and tag pushes. The coordinator brief says not to try `gh` | Topics in docs/topics.txt, description in docs/GITHUB_ABOUT.md, release SHA in CHANGELOG.md | See docs/HUMAN_STEPS.md |
| `main` on GitHub | origin was empty. The brief says never create `main` | Branch starts from its own first commit | Create `main` before the PR (docs/HUMAN_STEPS.md) |

Bug triage (frequency x severity):

| Finding | Score | Kind | Status |
| --- | --- | --- | --- |
| Percent values could be substrings of each other ("4.5" in "14.5"), which would count false leaks | 3 x 4 = 12 | live bug | fixed: fixed-width values, test `test_fact_values_are_unique` |

## MiniLM rows are not in the offline leak gate (2026-11-20)

The outside check found that `tests/test_leaks.py` runs the hybrid and dense paths with the hash
embedder. The MiniLM model needs a download, so `./init.sh` cannot use it offline. Fallback: the
MiniLM hybrid rows in `results/final-seed2.json` and `results/dev-seed1.json` came from the same
`evaluate.run` code with MiniLM, and they show zero leaks for modes 1 and 2. Manual step: none
needed. Anyone can rerun them with the commands in the README.
