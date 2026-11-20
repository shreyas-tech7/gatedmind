"""Shared seed 1 fixtures. Seed 2 is never touched by tests."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from gatedmind import org as orgmod
from gatedmind import questions as qmod

ROOT = Path(__file__).resolve().parents[1]


@lru_cache(maxsize=1)
def seed1():
    return orgmod.load(ROOT / "data/seed1/org.json"), qmod.load(ROOT / "data/seed1/questions.json")
