from __future__ import annotations

import random
from dataclasses import dataclass

from .infra.cache import TtlCache
from .infra.clock import SystemClock
from .infra.dns import DnsResolver
from .infra.ports import Clock, MxAnswer, Resolver, SmtpProber
from .infra.ratelimit import DomainRateLimiter
from .infra.smtp_client import AioSmtpProber
from .models import CatchAllCheck, MxCheck
from .options import Options
from .providers import EmailProvider, ProviderRegistry

MxEntry = tuple[MxCheck, EmailProvider, MxAnswer]


@dataclass
class Runtime:
    options: Options
    resolver: Resolver
    prober: SmtpProber
    clock: Clock
    registry: ProviderRegistry
    limiter: DomainRateLimiter
    mx_cache: TtlCache[str, MxEntry]
    catch_all_cache: TtlCache[str, CatchAllCheck]

    @classmethod
    def build(cls, options: Options) -> Runtime:
        clock = options.clock or SystemClock()
        overrides = tuple(p for p in options.provider_overrides if isinstance(p, EmailProvider))
        return cls(
            options=options,
            resolver=options.resolver or DnsResolver(),
            prober=options.prober or AioSmtpProber(),
            clock=clock,
            registry=ProviderRegistry.load(overrides),
            limiter=DomainRateLimiter(clock, options.per_domain_rate),
            mx_cache=TtlCache(clock, options.mx_cache_ttl),
            catch_all_cache=TtlCache(clock, options.catch_all_cache_ttl),
        )

    def pick_proxy(self) -> str | None:
        proxy = self.options.proxy
        if proxy is None:
            return None
        if isinstance(proxy, str):
            return proxy
        return random.choice(proxy) if proxy else None
