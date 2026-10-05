from __future__ import annotations

import unicodedata
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class NameParts:
    first: str
    last: str
    middle: str = ""

    @property
    def first_initial(self) -> str:
        return self.first[:1]

    @property
    def last_initial(self) -> str:
        return self.last[:1]


def _ascii_fold(text: str) -> str:
    decomposed = unicodedata.normalize("NFKD", text)
    stripped = "".join(ch for ch in decomposed if not unicodedata.combining(ch))
    return "".join(ch for ch in stripped if ch.isalnum()).lower()


def parse_name(name: str) -> NameParts:
    cleaned = name.strip()
    if "," in cleaned:
        last, _, first = cleaned.partition(",")
        tokens = [first.strip(), last.strip()]
    else:
        tokens = cleaned.split()

    folded = [_ascii_fold(token) for token in tokens if _ascii_fold(token)]
    if not folded:
        return NameParts(first="", last="")
    if len(folded) == 1:
        return NameParts(first=folded[0], last="")
    return NameParts(first=folded[0], last=folded[-1], middle=" ".join(folded[1:-1]))


@dataclass(frozen=True)
class Pattern:
    key: str
    build: Callable[[NameParts], str | None]


def _needs(*values: str) -> bool:
    return all(values)


_PATTERNS: tuple[Pattern, ...] = (
    Pattern("{first}.{last}", lambda p: f"{p.first}.{p.last}" if _needs(p.first, p.last) else None),
    Pattern("{first}{last}", lambda p: f"{p.first}{p.last}" if _needs(p.first, p.last) else None),
    Pattern(
        "{first_initial}{last}",
        lambda p: f"{p.first_initial}{p.last}" if _needs(p.first_initial, p.last) else None,
    ),
    Pattern("{first}", lambda p: p.first or None),
    Pattern("{first}_{last}", lambda p: f"{p.first}_{p.last}" if _needs(p.first, p.last) else None),
    Pattern("{first}-{last}", lambda p: f"{p.first}-{p.last}" if _needs(p.first, p.last) else None),
    Pattern(
        "{last}{first_initial}",
        lambda p: f"{p.last}{p.first_initial}" if _needs(p.last, p.first_initial) else None,
    ),
    Pattern("{last}.{first}", lambda p: f"{p.last}.{p.first}" if _needs(p.last, p.first) else None),
    Pattern(
        "{first_initial}.{last}",
        lambda p: f"{p.first_initial}.{p.last}" if _needs(p.first_initial, p.last) else None,
    ),
    Pattern("{last}", lambda p: p.last or None),
)


def catalogue() -> tuple[Pattern, ...]:
    return _PATTERNS


def by_key(key: str) -> Pattern | None:
    return next((pattern for pattern in _PATTERNS if pattern.key == key), None)


def matching_keys(parts: NameParts, local: str) -> list[str]:
    return [pattern.key for pattern in _PATTERNS if pattern.build(parts) == local]
