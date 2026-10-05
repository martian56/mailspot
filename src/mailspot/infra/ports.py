from __future__ import annotations

from dataclasses import dataclass, field
from typing import Protocol, runtime_checkable


@dataclass(frozen=True)
class MxAnswer:
    hosts: tuple[str, ...] = ()
    domain_exists: bool = True
    null_mx: bool = False
    implicit_a: bool = False
    transient_error: bool = False

    @property
    def found(self) -> bool:
        return bool(self.hosts) and not self.null_mx


@dataclass(frozen=True)
class SmtpReply:
    connected: bool
    code: int | None = None
    message: str = ""
    error: str = ""
    transcript: tuple[tuple[str, int | None], ...] = field(default_factory=tuple)


@runtime_checkable
class Resolver(Protocol):
    async def resolve_mx(self, domain: str, *, timeout: float) -> MxAnswer: ...


@runtime_checkable
class SmtpProber(Protocol):
    async def probe(
        self,
        host: str,
        recipient: str,
        *,
        helo: str,
        mail_from: str,
        timeout: float,
        proxy: str | None,
    ) -> SmtpReply: ...


@runtime_checkable
class Clock(Protocol):
    def now(self) -> float: ...

    async def sleep(self, seconds: float) -> None: ...
