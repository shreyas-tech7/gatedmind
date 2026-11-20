# Handover

Branch: `claude/build-gatedmind`. Resume with the launcher in docs/build/BUILD_PROMPT.md section 13.

Done: see PROGRESS.md. Next: the first feature in feature_list.json with `"passes": false`.

Commands:

```bash
./init.sh
python scripts/fetch_model.py            # MiniLM for hybrid runs
.venv/bin/gatedmind eval --seed 1 --retrievers bm25,hybrid --out results/dev-seed1.json
```

Open decisions: none.
