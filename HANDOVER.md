# Handover

Branch: `claude/build-gatedmind`. Resume with the launcher in docs/build/BUILD_PROMPT.md section 13.

State: every feature in feature_list.json passes. The build is complete. What is left is in
docs/HUMAN_STEPS.md: create `main`, open and merge the pull request, tag v0.1.0-rc1, make the
repo public when ready.

Commands:

```bash
./init.sh
python scripts/fetch_model.py            # MiniLM for hybrid runs
.venv/bin/gatedmind eval --seed 1 --retrievers bm25,hybrid --out results/dev-seed1.json
.venv/bin/python scripts/mcp_smoke.py
```

Do not rerun seed 2 to tune anything. It is the held-out seed. If a change touches enforcement,
generate seed 3 with `--final` for new final numbers and report every run.

Open decisions: none.
