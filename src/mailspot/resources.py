from __future__ import annotations

from functools import cache
from importlib.resources import files


def read_text(name: str) -> str:
    return (files("mailspot.data") / name).read_text(encoding="utf-8")


@cache
def read_lines(name: str) -> frozenset[str]:
    out: set[str] = set()
    for raw in read_text(name).splitlines():
        line = raw.strip().lower()
        if line and not line.startswith("#"):
            out.add(line)
    return frozenset(out)
