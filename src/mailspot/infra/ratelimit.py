from __future__ import annotations

import asyncio

from .ports import Clock


class DomainRateLimiter:
    def __init__(self, clock: Clock, per_domain_rate: float) -> None:
        self._clock = clock
        self._base_interval = 1.0 / per_domain_rate
        self._next_allowed: dict[str, float] = {}
        self._penalty: dict[str, float] = {}
        self._locks: dict[str, asyncio.Lock] = {}

    async def acquire(self, domain: str) -> None:
        lock = self._locks.setdefault(domain, asyncio.Lock())
        async with lock:
            now = self._clock.now()
            earliest = self._next_allowed.get(domain, now)
            wait = earliest - now
            if wait > 0:
                await self._clock.sleep(wait)
            interval = self._base_interval * self._penalty.get(domain, 1.0)
            self._next_allowed[domain] = self._clock.now() + interval

    def penalize(self, domain: str) -> None:
        current = self._penalty.get(domain, 1.0)
        self._penalty[domain] = min(current * 2.0, 16.0)

    def relax(self, domain: str) -> None:
        self._penalty.pop(domain, None)
