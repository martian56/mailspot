from __future__ import annotations

from .checks.catch_all import check_catch_all
from .checks.classify import classify
from .checks.mx import check_mx
from .checks.smtp import probe_mailbox
from .checks.syntax import check_syntax
from .evidence import Evidence
from .models import (
    CatchAllCheck,
    Checks,
    Flags,
    MxCheck,
    SmtpCheck,
    Status,
    SyntaxCheck,
    VerificationResult,
)
from .providers import DefaultProvider, EmailProvider
from .runtime import MxEntry, Runtime
from .scoring import score
from .suggest import suggest


async def verify_one(email: str, runtime: Runtime) -> VerificationResult:
    syntax = check_syntax(email, registry=runtime.registry)
    suggestion = suggest(email)

    if not syntax.valid:
        return _assemble(email, _invalid_syntax_evidence(email, syntax, suggestion))

    local, _, domain = syntax.normalized.rpartition("@")
    flags = classify(local, domain, runtime.options)
    mx, provider, answer = await _resolve_mx(domain, runtime)

    catch_all = CatchAllCheck()
    smtp = SmtpCheck()
    deferred = False

    if mx.found and not answer.transient_error:
        host = mx.hosts[0]
        proxy = runtime.pick_proxy()
        catch_all = await _detect_catch_all(domain, host, provider, runtime, proxy)
        smtp, deferred = await _probe(
            domain, host, syntax.normalized, provider, catch_all, runtime, proxy
        )

    evidence = Evidence(
        email=email,
        normalized=syntax.normalized,
        canonical=syntax.canonical,
        suggestion=suggestion,
        syntax=syntax,
        flags=flags,
        mx=mx,
        mx_answer=answer,
        provider=provider,
        catch_all=catch_all,
        smtp=smtp,
        deferred=deferred,
    )
    return _assemble(email, evidence)


async def _resolve_mx(domain: str, runtime: Runtime) -> MxEntry:
    async def factory() -> MxEntry:
        return await check_mx(
            domain, runtime.resolver, runtime.registry, timeout=runtime.options.dns_timeout
        )

    return await runtime.mx_cache.get_or_create(domain, factory)


async def _detect_catch_all(
    domain: str, host: str, provider: EmailProvider, runtime: Runtime, proxy: str | None
) -> CatchAllCheck:
    options = runtime.options
    if not (options.smtp_enabled and options.catch_all_enabled and provider.verifiable):
        return CatchAllCheck()

    async def factory() -> CatchAllCheck:
        await runtime.limiter.acquire(domain)
        return await check_catch_all(host, domain, runtime.prober, options, proxy=proxy)

    return await runtime.catch_all_cache.get_or_create(domain, factory)


async def _probe(
    domain: str,
    host: str,
    address: str,
    provider: EmailProvider,
    catch_all: CatchAllCheck,
    runtime: Runtime,
    proxy: str | None,
) -> tuple[SmtpCheck, bool]:
    reason = _smtp_skip_reason(runtime, provider, catch_all)
    if reason is not None:
        return SmtpCheck(attempted=False, skipped_reason=reason), False

    await runtime.limiter.acquire(domain)
    smtp, deferred = await probe_mailbox(
        host, address, runtime.prober, runtime.clock, runtime.options, proxy=proxy
    )
    if deferred:
        runtime.limiter.penalize(domain)
    else:
        runtime.limiter.relax(domain)
    return smtp, deferred


def _smtp_skip_reason(
    runtime: Runtime, provider: EmailProvider, catch_all: CatchAllCheck
) -> str | None:
    if not runtime.options.smtp_enabled:
        return "SMTP verification is disabled"
    if not provider.verifiable:
        label = provider.name or "this provider"
        return f"{label} accepts every probe and does not expose mailbox existence"
    if catch_all.is_catch_all is True:
        return "the domain is accept-all"
    return None


def _invalid_syntax_evidence(email: str, syntax: SyntaxCheck, suggestion: str | None) -> Evidence:
    return Evidence(
        email=email,
        normalized="",
        canonical="",
        suggestion=suggestion,
        syntax=syntax,
        flags=Flags(),
        mx=MxCheck(),
        mx_answer=None,
        provider=DefaultProvider(),
        catch_all=CatchAllCheck(),
        smtp=SmtpCheck(),
        deferred=False,
    )


def _assemble(email: str, evidence: Evidence) -> VerificationResult:
    result = score(evidence)
    reason = result.reason
    if result.status is Status.UNKNOWN and evidence.smtp.skipped_reason:
        reason = f"{evidence.smtp.skipped_reason}; result rests on syntax and MX only"

    return VerificationResult(
        email=email,
        canonical=evidence.canonical,
        status=result.status,
        decision=result.decision,
        confidence=result.confidence,
        provider=evidence.provider.name,
        deferred=evidence.deferred,
        suggestion=evidence.suggestion,
        checks=Checks(
            syntax=evidence.syntax,
            mx=evidence.mx,
            smtp=evidence.smtp,
            catch_all=evidence.catch_all,
        ),
        flags=evidence.flags,
        reason=reason,
    )
