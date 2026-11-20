"""Start the MCP server over stdio with the official client and call each tool."""

import importlib.util
from pathlib import Path

import anyio

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("mcp_smoke", ROOT / "scripts" / "mcp_smoke.py")
smoke_mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(smoke_mod)


def test_mcp_server_over_stdio(seed1_index, tmp_path):
    index_path = Path(seed1_index.con.execute("PRAGMA database_list").fetchone()[2])
    audit = tmp_path / "audit.jsonl"
    res = anyio.run(smoke_mod.smoke, index_path, audit)
    assert res["tools"] == ["get_doc", "search", "who_knows"]
    by = {(c["tool"], c["who"]): c for c in res["calls"]}
    assert not by[("get_doc", "allowed")]["is_error"]
    assert by[("get_doc", "forbidden")]["is_error"]
    target = by[("search", "allowed")]["target"]
    assert f'"{target}"' in by[("search", "allowed")]["text"]
    assert f'"{target}"' not in by[("search", "forbidden")]["text"]
    assert len(audit.read_text().splitlines()) == 6
