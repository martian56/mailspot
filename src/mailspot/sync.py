from __future__ import annotations

import asyncio
from collections.abc import Sequence

from . import api
from .finder import Sample
from .models import FinderResult, VerificationResult
from .options import Options


def verify(email: str, *, options: Options | None = None) -> VerificationResult:
    return asyncio.run(api.verify(email, options=options))


def find(
    name: str,
    domain: str,
    *,
    samples: Sequence[Sample] = (),
    options: Options | None = None,
) -> FinderResult:
    return asyncio.run(api.find(name, domain, samples=samples, options=options))


def verify_many(
    emails: Sequence[str], *, options: Options | None = None
) -> list[VerificationResult]:
    return asyncio.run(api.verify_many(emails, options=options))


def recheck(
    results: Sequence[VerificationResult], *, options: Options | None = None
) -> list[VerificationResult]:
    return asyncio.run(api.recheck(results, options=options))
