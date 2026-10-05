from __future__ import annotations

import contextlib
from collections.abc import Callable
from dataclasses import dataclass


@dataclass(frozen=True)
class Event:
    kind: str
    target: str
    detail: str = ""
    duration_ms: float | None = None


HookFn = Callable[[Event], None]


class Hooks:
    def __init__(self, *listeners: HookFn) -> None:
        self._listeners = listeners

    def emit(
        self,
        kind: str,
        target: str,
        detail: str = "",
        duration_ms: float | None = None,
    ) -> None:
        if not self._listeners:
            return
        event = Event(kind=kind, target=target, detail=detail, duration_ms=duration_ms)
        for listen in self._listeners:
            with contextlib.suppress(Exception):
                listen(event)
