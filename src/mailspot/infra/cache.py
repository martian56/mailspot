from __future__ import annotations

import asyncio
from collections.abc import Awaitable, Callable
from typing import Generic, TypeVar

from .ports import Clock

K = TypeVar("K")
V = TypeVar("V")


class TtlCache(Generic[K, V]):
    def __init__(self, clock: Clock, ttl: float) -> None:
        self._clock = clock
        self._ttl = ttl
        self._entries: dict[K, tuple[float, V]] = {}
        self._locks: dict[K, asyncio.Lock] = {}

    def get(self, key: K) -> V | None:
        entry = self._entries.get(key)
        if entry is None:
            return None
        expires_at, value = entry
        if self._clock.now() >= expires_at:
            self._entries.pop(key, None)
            return None
        return value

    def set(self, key: K, value: V) -> None:
        self._entries[key] = (self._clock.now() + self._ttl, value)

    async def get_or_create(self, key: K, factory: Callable[[], Awaitable[V]]) -> V:
        cached = self.get(key)
        if cached is not None:
            return cached
        lock = self._locks.setdefault(key, asyncio.Lock())
        async with lock:
            cached = self.get(key)
            if cached is not None:
                return cached
            value = await factory()
            self.set(key, value)
            return value
