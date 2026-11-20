"""Repo quality bar: README parts in order, generated numbers in sync, writing rules, files."""

import re
import struct
import subprocess
import sys
from pathlib import Path

import pytest

from gatedmind.report import write

ROOT = Path(__file__).resolve().parents[1]
FENCE = re.compile(r"```.*?```", re.S)
CODE = re.compile(r"`[^`]*`")
SECTIONS = [
    "## The problem",
    "## How it works",
    "## Results",
    "## Cost per task",
    "## Run it in 10 minutes",
    "## Limits",
    "## Glossary",
    "## Related work",
    "## How this was built",
]


def test_readme_parts_in_order():
    text = (ROOT / "README.md").read_text()
    assert text.splitlines()[4].startswith("**Status:**")
    pos = [text.index(s) for s in SECTIONS]
    assert pos == sorted(pos)
    assert "```mermaid" in text and "badge.svg" in text
    assert "not a security product" in text and "not real sign-in" in text
    assert "docs/build/BUILD_PROMPT.md" in text and "not done yet" in text


def test_readme_numbers_match_results_files():
    """Broken case: someone types a number into the README by hand."""
    assert (ROOT / "results" / "final-seed2.json").exists(), "final run missing"
    assert write(ROOT, check=True) == []
    text = (ROOT / "README.md").read_text()
    assert "3/200 = 1.5%" in text


def _prose(path: Path) -> str:
    return CODE.sub("", FENCE.sub("", path.read_text(encoding="utf-8")))


DOCS = [ROOT / "README.md", ROOT / "CONTRIBUTING.md"] + [
    p for p in (ROOT / "docs").glob("*.md") if p.name not in {"DEMO.md"}
]


@pytest.mark.parametrize("path", DOCS, ids=lambda p: p.name)
def test_writing_rules(path):
    text = _prose(path)
    assert "—" not in text and "–" not in text, "no em or en dashes"
    assert " - " not in text.replace("\n- ", "\n"), "no dashes as punctuation"
    for line in text.splitlines():
        if not line.startswith("|"):
            assert ";" not in line, f"semicolon in prose: {line}"
    for bad in ("it is important to note", "testament", "pivotal", "seamless", "delve"):
        assert bad not in text.lower()


def test_ship_files():
    for f in [
        "LICENSE",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        ".env.example",
        ".github/workflows/ci.yml",
        ".github/ISSUE_TEMPLATE/bug_report.md",
        "docs/index.html",
        "docs/DEMO.md",
        "docs/topics.txt",
        "docs/GITHUB_ABOUT.md",
        "docs/WALKTHROUGH.md",
        "docs/INTERVIEW_QA.md",
        "docs/HUMAN_STEPS.md",
        "docs/handoff/COWORK_PROMPT.md",
        "docs/SECURITY_CHECKS.md",
        "docs/build/BUILD_PROMPT.md",
    ]:
        assert (ROOT / f).is_file(), f
    assert "Copyright (c) 2026 Shreyas" in (ROOT / "LICENSE").read_text()


def test_social_preview_size():
    head = (ROOT / "docs" / "social-preview.png").read_bytes()[:24]
    assert struct.unpack(">II", head[16:24]) == (1280, 640)


def test_topics():
    topics = (ROOT / "docs" / "topics.txt").read_text().split()
    assert 5 <= len(topics) <= 20
    assert all(re.fullmatch(r"[a-z0-9][a-z0-9-]{0,24}", t) for t in topics)


def test_link_check_passes():
    r = subprocess.run(  # noqa: S603 (fixed argv, our own script)
        [sys.executable, str(ROOT / "scripts" / "check_links.py")],
        capture_output=True,
        text=True,
        timeout=60,
    )
    assert r.returncode == 0, r.stdout
