from __future__ import annotations

from collections.abc import Sequence

from .engine import verify_one
from .errors import ConfigurationError
from .models import Candidate, FinderMethod, FinderResult, Status, VerificationResult
from .normalize import split_address
from .patterns import NameParts, catalogue, matching_keys, parse_name
from .patterns import by_key as pattern_by_key
from .resources import read_lines
from .runtime import Runtime

Sample = tuple[str, str]


def _cannot_distinguish(result: VerificationResult) -> bool:
    smtp = result.checks.smtp
    return (
        result.checks.catch_all.is_catch_all is True
        or not smtp.attempted
        or smtp.deliverable is None
    )


def _detect_pattern(samples: Sequence[Sample]) -> str | None:
    consensus: set[str] | None = None
    for raw_name, raw_email in samples:
        parts = parse_name(raw_name)
        local = _local_of(raw_email)
        if local is None:
            continue
        keys = set(matching_keys(parts, local))
        consensus = keys if consensus is None else (consensus & keys)
    if consensus and len(consensus) == 1:
        return next(iter(consensus))
    return None


def _local_of(email: str) -> str | None:
    parts = split_address(email)
    if parts is None:
        return None
    return parts[0].lower()


def _ordered_locals(parts: NameParts, detected: str | None) -> list[tuple[str, str]]:
    ordered: list[tuple[str, str]] = []
    seen: set[str] = set()

    def add(key: str) -> None:
        pattern = pattern_by_key(key)
        if pattern is None:
            return
        local = pattern.build(parts)
        if local and local not in seen:
            seen.add(local)
            ordered.append((key, local))

    if detected is not None:
        add(detected)
    for pattern in catalogue():
        add(pattern.key)
    return ordered


async def find_one(
    name: str, domain: str, samples: Sequence[Sample], runtime: Runtime
) -> FinderResult:
    domain = domain.lower().rstrip(".")
    if domain in read_lines("free.txt"):
        raise ConfigurationError(
            "a free-provider domain has no company pattern to find against"
        )

    parts = parse_name(name)
    detected = _detect_pattern(samples)
    method = FinderMethod.PATTERN_DETECTED if detected else FinderMethod.PERMUTATION

    candidates: list[Candidate] = []
    best: Candidate | None = None
    for index, (key, local) in enumerate(_ordered_locals(parts, detected)):
        result = await verify_one(f"{local}@{domain}", runtime)
        candidate = Candidate(email=f"{local}@{domain}", pattern=key, result=result)
        candidates.append(candidate)
        if result.status is Status.VALID:
            best = candidate
            break
        if index == 0 and _cannot_distinguish(result):
            best = candidate
            break

    return FinderResult(
        name=name,
        domain=domain,
        best=best,
        candidates=candidates,
        detected_pattern=detected,
        method=method,
    )
