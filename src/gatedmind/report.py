"""Write the README result blocks and docs/index.html from the results files.

Nobody types a number into the README. `gatedmind readme` rewrites the text between the
`<!-- gm:NAME:start -->` and `<!-- gm:NAME:end -->` markers, and `--check` fails if the
README does not match the results files.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path

from .modes import MODES, NUMBER

LABEL = {
    "prefilter": "1 pre-filter",
    "postfilter": "2 post-filter",
    "redact": "3 redact after",
    "none": "4 none (control)",
}
RETRIEVER_LABEL = {"bm25": "BM25", "dense": "MiniLM dense", "hybrid": "BM25 + MiniLM (RRF)"}


def pct(x: float) -> str:
    return f"{100 * x:.1f}%"


def rate(r: dict) -> str:
    p, lo, hi = r["ci"]
    return f"{pct(p)} [{pct(lo)}, {pct(hi)}] ({r['k']}/{r['n']})"


def ms(v: float, ci: list[float]) -> str:
    return f"{v:.2f} [{ci[0]:.2f}, {ci[1]:.2f}]"


def table(res: dict) -> str:
    head = (
        "| Mode | Retriever | Accuracy | Leak rate | Over-blocking | Chunks to model | "
        "Latency p50 ms | Latency p95 ms |\n| --- | --- | --- | --- | --- | --- | --- | --- |"
    )
    rows = []
    for ret, r in res["retrievers"].items():
        for m in MODES:
            s = r["modes"][m]
            rows.append(
                f"| {LABEL[m]} | {RETRIEVER_LABEL.get(ret, ret)} | {rate(s['accuracy'])} | "
                f"{rate(s['leak_rate'])} | {rate(s['overblock_rate'])} | "
                f"{s['chunks_to_model_mean']:.2f} | {ms(s['latency_p50_ms'], s['latency_p50_ci'])} | "
                f"{ms(s['latency_p95_ms'], s['latency_p95_ci'])} |"
            )
    return "\n".join([head, *rows])


def meta(res: dict, path: str) -> str:
    return (
        f"Seed {res['seed']}, run on {res['date']} with the {res['model']}. "
        f"{res['n_questions']} questions, {res['n_docs']} documents, {res['n_people']} people, "
        f"top {res['k']} chunks. CPU: {res['cpu']}, {res['cores_used']} core, Python "
        f"{res['python']}. Source: [`{path}`]({path}). Brackets hold 95% intervals: Wilson for "
        "rates, bootstrap for latency."
    )


def zero_leak_text(res: dict) -> str:
    lines = []
    for ret, r in res["retrievers"].items():
        for m in ("prefilter", "postfilter"):
            s = r["modes"][m]
            n, k = s["leak_rate"]["n"], s["leak_rate"]["k"]
            if k == 0:
                lines.append(
                    f"- Mode {NUMBER[m]} with {RETRIEVER_LABEL.get(ret, ret)}: 0 leaks in {n} "
                    f"questions. The 95% upper bound by the rule of three is 3/{n} = "
                    f"{pct(s['leak_upper_rule_of_three'])}. The Wilson upper bound is "
                    f"{pct(s['leak_rate']['ci'][2])}."
                )
            else:
                lines.append(f"- Mode {NUMBER[m]} with {RETRIEVER_LABEL.get(ret, ret)}: {k} leaks.")
    return "\n".join(lines)


def cost(res: dict) -> str:
    r = res["retrievers"]
    parts = []
    for ret in r:
        s = r[ret]["modes"]["prefilter"]
        parts.append(f"{s['latency_p50_ms']:.2f} ms median with {RETRIEVER_LABEL.get(ret, ret)}")
    return (
        "Each question costs $0.00 in API fees, because the model is a local script and the "
        "embedder runs on the CPU. Mode 1 takes " + " and ".join(parts) + f" on {res['cpu']}."
    )


def blocks(final: dict, dev: dict, final_path: str, dev_path: str) -> dict[str, str]:
    return {
        "results": table(final) + "\n\n" + meta(final, final_path),
        "zeroleaks": zero_leak_text(final),
        "cost": cost(final),
        "dev": table(dev) + "\n\n" + meta(dev, dev_path),
    }


def render(text: str, values: dict[str, str]) -> str:
    for name, body in values.items():
        pat = re.compile(rf"(<!-- gm:{name}:start -->\n).*?(\n<!-- gm:{name}:end -->)", re.S)
        if not pat.search(text):
            raise ValueError(f"marker gm:{name} missing")
        text = pat.sub(lambda m, b=body: m.group(1) + b + m.group(2), text)
    return text


def page(final: dict, path: str) -> str:
    rows = []
    for ret, r in final["retrievers"].items():
        for m in MODES:
            s = r["modes"][m]
            cells = [
                LABEL[m],
                RETRIEVER_LABEL.get(ret, ret),
                rate(s["accuracy"]),
                rate(s["leak_rate"]),
                rate(s["overblock_rate"]),
                f"{s['latency_p50_ms']:.2f}",
                f"{s['latency_p95_ms']:.2f}",
            ]
            leak = s["leak_rate"]["k"] > 0
            tds = "".join(f"<td>{html.escape(c)}</td>" for c in cells)
            rows.append(f'<tr class="{"leak" if leak else "ok"}">{tds}</tr>')
    return f"""<!doctype html>
<html lang="en"><head><meta charset="utf-8"><title>gatedmind results</title>
<meta name="viewport" content="width=device-width, initial-scale=1">
<style>
body {{ font: 15px/1.5 system-ui, sans-serif; margin: 2rem auto; max-width: 64rem; padding: 0 1rem;
  background: #0d1117; color: #e6edf3; }}
table {{ border-collapse: collapse; width: 100%; }} td, th {{ border: 1px solid #30363d; padding: .4rem; }}
tr.leak td:nth-child(4) {{ color: #f85149; }} tr.ok td:nth-child(4) {{ color: #3fb950; }}
a {{ color: #6ea8ff; }}
</style></head><body>
<h1 id="top">gatedmind results</h1>
<p>A demo, not a security product. Leak rate per enforcement mode on seed {final["seed"]},
{final["n_questions"]} questions, run on {html.escape(final["date"])} with the
{html.escape(final["model"])}. Brackets hold 95% intervals.</p>
<table><tr><th>Mode</th><th>Retriever</th><th>Accuracy</th><th>Leak rate</th>
<th>Over-blocking</th><th>p50 ms</th><th>p95 ms</th></tr>
{chr(10).join(rows)}
</table>
<p>Numbers come from <a href="../{path}">{path}</a>. See the <a href="../README.md">README</a>.</p>
</body></html>
"""


def write(root: Path, check: bool = False) -> list[str]:
    final_path, dev_path = "results/final-seed2.json", "results/dev-seed1.json"
    if not (root / final_path).exists() or not (root / dev_path).exists():
        return []  # nothing to write before the final run
    final = json.loads((root / final_path).read_text())
    dev = json.loads((root / dev_path).read_text())
    targets = {
        root / "README.md": render(
            (root / "README.md").read_text(), blocks(final, dev, final_path, dev_path)
        ),
        root / "docs" / "index.html": page(final, final_path),
    }
    stale = []
    for p, new in targets.items():
        old = p.read_text() if p.exists() else ""
        if old != new:
            stale.append(str(p.relative_to(root)))
            if not check:
                p.write_text(new)
    return stale
