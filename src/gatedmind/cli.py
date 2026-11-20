"""Command line: generate, index, ask, eval, serve, tools-json and readme."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from . import evaluate, modes
from . import org as orgmod
from . import questions as qmod
from .embed import ROOT, cache_dir, get_embedder
from .index import Index, build
from .tools import TOOLS

FINAL_SEEDS = (
    "Seeds other than 1 are held out. Pass --final to use one, and only for the final run."
)


def data_dir(seed: int) -> Path:
    return ROOT / "data" / f"seed{seed}"


def guard_seed(seed: int, final: bool) -> None:
    if seed != 1 and not final:
        raise SystemExit(FINAL_SEEDS)


def load_seed(seed: int):
    d = data_dir(seed)
    if not (d / "org.json").exists():
        raise SystemExit(f"{d}/org.json missing. Run: gatedmind generate --seed {seed}")
    return orgmod.load(d / "org.json"), qmod.load(d / "questions.json")


def index_path(seed: int, embedder: str | None) -> Path:
    return cache_dir() / f"index-seed{seed}-{embedder or 'bm25'}.sqlite"


def open_index(seed: int, embedder: str | None = None, rebuild: bool = False) -> Index:
    org, _ = load_seed(seed)
    path = index_path(seed, embedder)
    emb = get_embedder(embedder) if embedder else None
    if rebuild or not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        build(org, path, emb)
    return Index(path, emb)


RETRIEVER_EMBEDDER = {"bm25": None, "dense": "minilm", "hybrid": "minilm"}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        prog="gatedmind", description="Permission-aware RAG leak benchmark."
    )
    sub = ap.add_subparsers(dest="cmd", required=True)
    g = sub.add_parser("generate", help="make the synthetic org and the questions for a seed")
    g.add_argument("--seed", type=int, default=1)
    g.add_argument("--final", action="store_true")
    i = sub.add_parser("index", help="build the SQLite index for a seed")
    i.add_argument("--seed", type=int, default=1)
    i.add_argument("--embedder", choices=["hash", "minilm"])
    i.add_argument("--final", action="store_true")
    a = sub.add_parser("ask", help="ask one question as a test identity")
    a.add_argument("question")
    a.add_argument("--as", dest="identity", required=True)
    a.add_argument("--mode", choices=modes.MODES, default="prefilter")
    a.add_argument("--seed", type=int, default=1)
    e = sub.add_parser("eval", help="run the suite through all four modes")
    e.add_argument("--seed", type=int, default=1)
    e.add_argument("--retrievers", default="bm25")
    e.add_argument("--out", type=Path)
    e.add_argument("--final", action="store_true")
    s = sub.add_parser("serve", help="run the MCP server over stdio")
    s.add_argument("--index", type=Path)
    s.add_argument("--seed", type=int, default=1)
    s.add_argument("--audit", type=Path)
    sub.add_parser("tools-json", help="print the MCP tool list as JSON")
    r = sub.add_parser("readme", help="write README and docs/index.html from results/")
    r.add_argument("--check", action="store_true")
    args = ap.parse_args(argv)

    if args.cmd == "generate":
        guard_seed(args.seed, args.final)
        org = orgmod.generate(args.seed)
        orgmod.save(org, data_dir(args.seed) / "org.json")
        qs = qmod.make_questions(org)
        qmod.save(qs, data_dir(args.seed) / "questions.json")
        print(
            f"seed {args.seed}: {len(org['docs'])} docs, {len(org['people'])} people, {len(qs)} questions"
        )
    elif args.cmd == "index":
        guard_seed(args.seed, args.final)
        ix = open_index(args.seed, args.embedder, rebuild=True)
        print(f"{index_path(args.seed, args.embedder)}: {len(ix.texts)} chunks")
    elif args.cmd == "ask":
        guard_seed(args.seed, False)
        ix = open_index(args.seed)
        if args.identity not in ix.people:
            raise SystemExit(f"unknown identity {args.identity}")
        res = modes.run(ix, args.identity, args.question, args.mode)
        print(res.answer)
        print(
            f"-- mode {modes.NUMBER[args.mode]} ({args.mode}), cited {res.cited}, "
            f"denied chunks {res.denied_chunks}"
        )
    elif args.cmd == "eval":
        guard_seed(args.seed, args.final)
        org, qs = load_seed(args.seed)
        names = [x for x in args.retrievers.split(",") if x]
        indexes = {n: open_index(args.seed, RETRIEVER_EMBEDDER[n], rebuild=True) for n in names}
        result = evaluate.run_all(org, qs, indexes)
        out = args.out or ROOT / "results" / f"seed{args.seed}.json"
        evaluate.save(result, out)
        for n, r in result["retrievers"].items():
            for m, s in r["modes"].items():
                print(
                    f"{n:7} {m:10} acc {s['accuracy']['k']:3}/{s['n']}  leaks "
                    f"{s['leak_rate']['k']:3}  overblock {s['overblock_rate']['k']:3}/"
                    f"{s['overblock_rate']['n']}  p50 {s['latency_p50_ms']:.2f} ms"
                )
        print("wrote", out)
    elif args.cmd == "serve":
        from .mcp_server import serve

        if args.index is None:
            guard_seed(args.seed, False)
        serve(args.index or _ensure(args.seed), args.audit)
    elif args.cmd == "tools-json":
        json.dump(TOOLS, sys.stdout, indent=1)
        print()
    elif args.cmd == "readme":
        from .report import write

        stale = write(ROOT, check=args.check)
        if args.check and stale:
            print("out of date:", ", ".join(stale))
            return 1
        print("up to date" if not stale else "wrote " + ", ".join(stale))
    return 0


def _ensure(seed: int) -> Path:
    open_index(seed)
    return index_path(seed, None)


if __name__ == "__main__":
    sys.exit(main())
