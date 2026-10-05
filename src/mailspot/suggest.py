from __future__ import annotations

from .normalize import split_address
from .resources import read_lines


def _damerau_levenshtein(a: str, b: str) -> int:
    if a == b:
        return 0
    len_a, len_b = len(a), len(b)
    if not len_a:
        return len_b
    if not len_b:
        return len_a

    previous = list(range(len_b + 1))
    before_previous = [0] * (len_b + 1)
    for i in range(1, len_a + 1):
        current = [i] + [0] * len_b
        for j in range(1, len_b + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            current[j] = min(
                current[j - 1] + 1,
                previous[j] + 1,
                previous[j - 1] + cost,
            )
            if i > 1 and j > 1 and a[i - 1] == b[j - 2] and a[i - 2] == b[j - 1]:
                current[j] = min(current[j], before_previous[j - 2] + 1)
        before_previous, previous = previous, current
    return previous[len_b]


def _closest(domain: str, candidates: frozenset[str]) -> tuple[str | None, int]:
    best: str | None = None
    best_distance = len(domain) + 1
    for candidate in candidates:
        distance = _damerau_levenshtein(domain, candidate)
        if distance < best_distance:
            best, best_distance = candidate, distance
    return best, best_distance


def suggest(email: str) -> str | None:
    parts = split_address(email)
    if parts is None:
        return None
    local, domain = parts
    domain = domain.lower().rstrip(".")

    known = read_lines("common_domains.txt")
    if domain in known:
        return None

    best, distance = _closest(domain, known)
    threshold = 2 if len(domain) >= 10 else 1
    if best is not None and 1 <= distance <= threshold:
        return f"{local}@{best}"
    return None
