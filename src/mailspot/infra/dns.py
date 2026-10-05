from __future__ import annotations

import dns.asyncresolver
import dns.exception
import dns.resolver

from .ports import MxAnswer

_NULL_EXCHANGES = {"", "."}


class DnsResolver:
    async def resolve_mx(self, domain: str, *, timeout: float) -> MxAnswer:
        try:
            answer = await dns.asyncresolver.resolve(domain, "MX", lifetime=timeout)
        except dns.resolver.NXDOMAIN:
            return MxAnswer(domain_exists=False)
        except dns.resolver.NoAnswer:
            return await self._address_fallback(domain, timeout)
        except (dns.resolver.NoNameservers, dns.exception.Timeout):
            return MxAnswer(transient_error=True)

        records = sorted(answer, key=lambda record: record.preference)
        exchanges = [str(record.exchange).rstrip(".") for record in records]
        if len(exchanges) == 1 and exchanges[0] in _NULL_EXCHANGES:
            return MxAnswer(null_mx=True)
        hosts = tuple(host for host in exchanges if host not in _NULL_EXCHANGES)
        return MxAnswer(hosts=hosts)

    async def _address_fallback(self, domain: str, timeout: float) -> MxAnswer:
        for record_type in ("A", "AAAA"):
            try:
                await dns.asyncresolver.resolve(domain, record_type, lifetime=timeout)
            except (dns.resolver.NoAnswer, dns.resolver.NXDOMAIN):
                continue
            except (dns.resolver.NoNameservers, dns.exception.Timeout):
                return MxAnswer(transient_error=True)
            else:
                return MxAnswer(hosts=(domain,), implicit_a=True)
        return MxAnswer()
