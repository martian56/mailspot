from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass, field, replace
from typing import Any

from .errors import ConfigurationError
from .infra.hooks import Hooks
from .infra.ports import Clock, Resolver, SmtpProber


@dataclass(frozen=True)
class ProbeIdentity:
    helo: str = "mailspot.local"
    mail_from: str = "verify@mailspot.local"


@dataclass(frozen=True)
class Options:
    smtp_enabled: bool = True
    catch_all_enabled: bool = True
    concurrency: int = 50
    per_domain_rate: float = 5.0
    dns_timeout: float = 5.0
    smtp_timeout: float = 10.0
    connect_timeout: float = 10.0
    smtp_retries: int = 1
    mx_cache_ttl: float = 3600.0
    catch_all_cache_ttl: float = 3600.0
    probe_identity: ProbeIdentity = field(default_factory=ProbeIdentity)
    extra_disposable: frozenset[str] = frozenset()
    extra_free: frozenset[str] = frozenset()
    extra_roles: frozenset[str] = frozenset()
    proxy: str | tuple[str, ...] | None = None
    hooks: Hooks = field(default_factory=Hooks)
    provider_overrides: Sequence[object] = ()
    providers: Sequence[object] = ()
    resolver: Resolver | None = None
    prober: SmtpProber | None = None
    clock: Clock | None = None

    def __post_init__(self) -> None:
        if self.concurrency < 1:
            raise ConfigurationError("concurrency must be at least 1")
        if self.per_domain_rate <= 0:
            raise ConfigurationError("per_domain_rate must be greater than 0")
        if self.smtp_retries < 0:
            raise ConfigurationError("smtp_retries cannot be negative")
        for name in ("dns_timeout", "smtp_timeout", "connect_timeout"):
            if getattr(self, name) <= 0:
                raise ConfigurationError(f"{name} must be greater than 0")

    def with_(self, **changes: Any) -> Options:
        return replace(self, **changes)
