from __future__ import annotations

import asyncio
from collections.abc import AsyncIterator, Sequence

from .engine import verify_one
from .finder import Sample, find_one
from .models import FinderResult, VerificationResult
from .options import Options
from .runtime import Runtime


async def verify(email: str, *, options: Options | None = None) -> VerificationResult:
    runtime = Runtime.build(options or Options())
    return await verify_one(email, runtime)


async def find(
    name: str,
    domain: str,
    *,
    samples: Sequence[Sample] = (),
    options: Options | None = None,
) -> FinderResult:
    runtime = Runtime.build(options or Options())
    return await find_one(name, domain, samples, runtime)


async def verify_many(
    emails: Sequence[str], *, options: Options | None = None
) -> list[VerificationResult]:
    runtime = Runtime.build(options or Options())
    semaphore = asyncio.Semaphore(runtime.options.concurrency)

    grouped: dict[str, list[int]] = {}
    for index, email in enumerate(emails):
        grouped.setdefault(email, []).append(index)

    async def run(email: str) -> VerificationResult:
        async with semaphore:
            return await verify_one(email, runtime)

    tasks = {email: asyncio.create_task(run(email)) for email in grouped}
    results: list[VerificationResult | None] = [None] * len(emails)
    for email, positions in grouped.items():
        result = await tasks[email]
        for position in positions:
            results[position] = result
    return [r for r in results if r is not None]


async def verify_stream(
    emails: Sequence[str], *, options: Options | None = None
) -> AsyncIterator[tuple[int, VerificationResult]]:
    runtime = Runtime.build(options or Options())
    semaphore = asyncio.Semaphore(runtime.options.concurrency)

    async def run(index: int, email: str) -> tuple[int, VerificationResult]:
        async with semaphore:
            return index, await verify_one(email, runtime)

    tasks = [asyncio.create_task(run(i, e)) for i, e in enumerate(emails)]
    for completed in asyncio.as_completed(tasks):
        yield await completed


async def recheck(
    results: Sequence[VerificationResult], *, options: Options | None = None
) -> list[VerificationResult]:
    runtime = Runtime.build(options or Options())
    semaphore = asyncio.Semaphore(runtime.options.concurrency)
    updated = list(results)

    async def run(email: str) -> VerificationResult:
        async with semaphore:
            return await verify_one(email, runtime)

    pending = {
        index: asyncio.create_task(run(result.email))
        for index, result in enumerate(updated)
        if result.deferred
    }
    for index, task in pending.items():
        updated[index] = await task
    return updated
