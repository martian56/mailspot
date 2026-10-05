from __future__ import annotations

from ..infra.ports import MxAnswer, Resolver
from ..models import MxCheck
from ..providers import EmailProvider, ProviderRegistry


async def check_mx(
    domain: str,
    resolver: Resolver,
    registry: ProviderRegistry,
    *,
    timeout: float,
) -> tuple[MxCheck, EmailProvider, MxAnswer]:
    answer = await resolver.resolve_mx(domain, timeout=timeout)
    provider = registry.resolve(domain, answer.hosts)
    check = _build_check(answer, provider)
    return check, provider, answer


def _build_check(answer: MxAnswer, provider: EmailProvider) -> MxCheck:
    name = provider.name
    if answer.transient_error:
        return MxCheck(found=False, provider=name, reason="DNS lookup failed temporarily")
    if not answer.domain_exists:
        return MxCheck(found=False, provider=name, reason="the domain does not exist")
    if answer.null_mx:
        return MxCheck(
            found=False, null_mx=True, provider=name, reason="the domain accepts no mail"
        )
    if not answer.found:
        return MxCheck(found=False, provider=name, reason="the domain has no mail route")
    reason = "mail route via an address record" if answer.implicit_a else ""
    return MxCheck(found=True, hosts=list(answer.hosts), provider=name, reason=reason)
