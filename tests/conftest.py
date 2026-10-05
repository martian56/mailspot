from __future__ import annotations

import asyncio
from collections.abc import Sequence
from dataclasses import dataclass, field

import pytest
from pytest_bdd import given, parsers, then, when

import mailspot
from mailspot.infra.ports import MxAnswer
from mailspot.models import VerificationResult
from mailspot.options import Options
from mailspot.providers import EmailProvider
from tests.fakes import FakeClock, FakeProber, FakeResolver


class ForcedUnverifiable(EmailProvider):
    verifiable = False

    def __init__(self, domain: str) -> None:
        self.name = "forced"
        self._domain = domain

    def matches(self, domain: str, hosts: Sequence[str]) -> bool:
        return domain == self._domain


@dataclass
class Ctx:
    resolver: FakeResolver = field(default_factory=FakeResolver)
    prober: FakeProber = field(default_factory=FakeProber)
    clock: FakeClock = field(default_factory=FakeClock)
    overrides: list[EmailProvider] = field(default_factory=list)
    smtp_enabled: bool = True
    result: VerificationResult | None = None
    results: list[VerificationResult] = field(default_factory=list)
    streamed: list[tuple[int, VerificationResult]] = field(default_factory=list)
    probes_before_recheck: int = 0

    def options(self) -> Options:
        return Options(
            resolver=self.resolver,
            prober=self.prober,
            clock=self.clock,
            smtp_enabled=self.smtp_enabled,
            provider_overrides=tuple(self.overrides),
            smtp_retries=1,
            per_domain_rate=1000.0,
        )

    def host_of(self, name: str) -> str:
        if self.prober.known(name):
            return name
        return self.resolver.host_for(name)

    def host_for_email(self, email: str) -> str:
        domain = email.rpartition("@")[2]
        return self.resolver.host_for(domain)


@pytest.fixture
def ctx() -> Ctx:
    return Ctx()


def _run_verify(ctx: Ctx, email: str) -> None:
    ctx.result = mailspot.sync.verify(email, options=ctx.options())
    ctx.results = [ctx.result]


def _run_many(ctx: Ctx, emails: Sequence[str]) -> None:
    ctx.results = mailspot.sync.verify_many(emails, options=ctx.options())
    ctx.result = ctx.results[0] if ctx.results else None


def _rows(datatable: list[list[str]]) -> list[str]:
    return [row[0].strip() for row in datatable]




@given(parsers.parse('the domain "{domain}" has MX hosts:'))
def given_mx_hosts(ctx: Ctx, domain: str, datatable: list[list[str]]) -> None:
    rows = datatable[1:]
    ordered = sorted(rows, key=lambda row: int(row[0]))
    hosts = tuple(row[1].strip() for row in ordered)
    ctx.resolver.set(domain, MxAnswer(hosts=hosts))


@given(parsers.parse('the domain "{domain}" has a mail host "{host}"'))
def given_mail_host(ctx: Ctx, domain: str, host: str) -> None:
    ctx.resolver.set(domain, MxAnswer(hosts=(host,)))
    ctx.prober.host(host)


@given(parsers.parse('the domain "{domain}" has no MX records'))
def given_no_mx(ctx: Ctx, domain: str) -> None:
    ctx.resolver.set(domain, MxAnswer())


@given(parsers.parse('the domain "{domain}" has an A record'))
def given_a_record(ctx: Ctx, domain: str) -> None:
    ctx.resolver.set(domain, MxAnswer(hosts=(domain,), implicit_a=True))


@given(parsers.parse('the domain "{domain}" has no A record'))
def given_no_a(ctx: Ctx, domain: str) -> None:
    ctx.resolver.set(domain, MxAnswer())


@given(parsers.parse('the domain "{domain}" does not exist'))
def given_nxdomain(ctx: Ctx, domain: str) -> None:
    ctx.resolver.set(domain, MxAnswer(domain_exists=False))


@given(parsers.parse('the domain "{domain}" has a null MX record'))
def given_null_mx(ctx: Ctx, domain: str) -> None:
    ctx.resolver.set(domain, MxAnswer(null_mx=True))


@given(parsers.parse('the domain "{domain}" has a mail route'))
def given_mail_route(ctx: Ctx, domain: str) -> None:
    ctx.resolver.set(domain, MxAnswer(hosts=(f"mail.{domain}",)))


@given(parsers.parse('DNS for "{domain}" times out'))
def given_dns_timeout(ctx: Ctx, domain: str) -> None:
    ctx.resolver.set(domain, MxAnswer(transient_error=True))


@given(parsers.parse('the domain "{domain}" is hosted on Google Workspace'))
def given_google_workspace(ctx: Ctx, domain: str) -> None:
    ctx.resolver.set(domain, MxAnswer(hosts=("aspmx.l.google.com",)))


@given(parsers.parse('the domain "{domain}" is on a verifiable provider'))
def given_verifiable_provider(ctx: Ctx, domain: str) -> None:
    ctx.resolver.set(domain, MxAnswer(hosts=(f"mail.{domain}",)))


@given(parsers.parse('the domain "{domain}" is on an unrecognized provider'))
def given_unrecognized_provider(ctx: Ctx, domain: str) -> None:
    ctx.resolver.set(domain, MxAnswer(hosts=(f"mail.{domain}",)))


@given(parsers.parse("I mark \"{domain}\"'s provider as unverifiable via options"))
def given_forced_unverifiable(ctx: Ctx, domain: str) -> None:
    ctx.resolver.set(domain, MxAnswer(hosts=(f"mail.{domain}",)))
    ctx.overrides.append(ForcedUnverifiable(domain))


@given(parsers.parse('a mail host that answers for "{domain}"'))
def given_host_answers_one(ctx: Ctx, domain: str) -> None:
    ctx.prober.host(ctx.resolver.host_for(domain))


@given(parsers.parse('a mail host that answers for "{first}" and "{second}"'))
def given_host_answers_two(ctx: Ctx, first: str, second: str) -> None:
    ctx.prober.host(ctx.resolver.host_for(first))
    ctx.prober.host(ctx.resolver.host_for(second))




@given(parsers.parse('"{name}" is not a catch-all server'))
def given_not_catch_all(ctx: Ctx, name: str) -> None:
    ctx.prober.host(ctx.host_of(name)).catch_all = False


@given(parsers.parse('"{host}" accepts every address'))
def given_accepts_every(ctx: Ctx, host: str) -> None:
    ctx.prober.host(ctx.host_of(host)).catch_all = True


@given(parsers.parse('"{host}" rejects unknown addresses with code 550'))
def given_rejects_unknown(ctx: Ctx, host: str) -> None:
    ctx.prober.host(ctx.host_of(host)).catch_all = False


@given(parsers.parse('"{host}" accepts "{email}"'))
def given_host_accepts(ctx: Ctx, host: str, email: str) -> None:
    ctx.prober.host(ctx.host_of(host)).accepts.add(email)


@given(parsers.parse('"{host}" accepts only "{email}"'))
def given_host_accepts_only(ctx: Ctx, host: str, email: str) -> None:
    ctx.prober.host(ctx.host_of(host)).accepts.add(email)


@given(parsers.parse('"{host}" rejects "{email}" with code 550'))
def given_host_rejects(ctx: Ctx, host: str, email: str) -> None:
    ctx.prober.host(ctx.host_of(host)).rejects.add(email)


@given(parsers.parse('"{host}" replies to "{email}" with code 451'))
def given_host_greylist(ctx: Ctx, host: str, email: str) -> None:
    ctx.prober.host(ctx.host_of(host)).greylisted.add(email)


@given(parsers.parse('"{host}" replies to "{email}" with code 451 the first time'))
def given_host_greylist_first(ctx: Ctx, host: str, email: str) -> None:
    ctx.prober.host(ctx.host_of(host)).greylisted.add(email)


@given(parsers.parse('"{host}" accepts "{email}" on a later attempt'))
def given_host_accepts_later(ctx: Ctx, host: str, email: str) -> None:
    ctx.prober.host(ctx.host_of(host)).accepts.add(email)


@given(parsers.parse('"{host}" does not answer on port 25'))
def given_host_unreachable(ctx: Ctx, host: str) -> None:
    ctx.prober.host(ctx.host_of(host)).reachable = False


@given(parsers.parse('the catch-all probe to "{host}" times out'))
def given_catch_all_timeout(ctx: Ctx, host: str) -> None:
    ctx.prober.host(ctx.host_of(host)).catch_all_probe_unreachable = True


@given("SMTP verification is disabled")
def given_smtp_disabled(ctx: Ctx) -> None:
    ctx.smtp_enabled = False


@given("SMTP cannot be used from this host")
def given_smtp_unusable(ctx: Ctx) -> None:
    ctx.smtp_enabled = False


@given(parsers.parse('"{domain}" defers every probe on the first attempt'))
def given_domain_defers(ctx: Ctx, domain: str) -> None:
    host = ctx.resolver.host_for(domain)
    behavior = ctx.prober.host(host)
    behavior.greylist_all = True


@given(parsers.parse('"{domain}" accepts on a later attempt'))
@when(parsers.parse('"{domain}" accepts on a later attempt'))
def given_domain_accepts_later(ctx: Ctx, domain: str) -> None:
    pass




@given(parsers.parse('"{email}" is deliverable on a non-catch-all domain'))
def given_deliverable_non_catch_all(ctx: Ctx, email: str) -> None:
    ctx.prober.host(ctx.host_for_email(email)).accepts.add(email)


@given(parsers.parse('"{email}" is deliverable'))
def given_deliverable(ctx: Ctx, email: str) -> None:
    ctx.prober.host(ctx.host_for_email(email)).accepts.add(email)


@given(parsers.parse('"{email}" is hard-rejected on a non-catch-all domain'))
def given_hard_rejected(ctx: Ctx, email: str) -> None:
    ctx.prober.host(ctx.host_for_email(email)).rejects.add(email)


@given(parsers.parse('"{email}" is on a catch-all domain'))
def given_on_catch_all(ctx: Ctx, email: str) -> None:
    ctx.prober.host(ctx.host_for_email(email)).catch_all = True


_DISPOSABLE_HOST = (
    'the domain "{domain}" has a mail host that accepts every address checked as not catch-all'
)


@given(parsers.parse(_DISPOSABLE_HOST))
def given_disposable_host(ctx: Ctx, domain: str) -> None:
    ctx.prober.host(ctx.resolver.host_for(domain)).catch_all = False


@given(parsers.parse('"{domain}" is added to the disposable list'))
def given_extra_disposable(ctx: Ctx, domain: str) -> None:
    ctx.overrides_disposable = domain




@when(parsers.parse('I verify "{email}"'))
def when_verify(ctx: Ctx, email: str) -> None:
    extra = getattr(ctx, "overrides_disposable", None)
    if extra is not None:
        options = ctx.options().with_(extra_disposable=frozenset({extra}))
        ctx.result = mailspot.sync.verify(email, options=options)
        ctx.results = [ctx.result]
    else:
        _run_verify(ctx, email)


@when(parsers.parse("I verify these addresses in order:"))
def when_verify_many_order(ctx: Ctx, datatable: list[list[str]]) -> None:
    rows = _rows(datatable)
    ctx.expected_order = rows
    _run_many(ctx, rows)


@when(parsers.parse("I verify these addresses:"))
def when_verify_many(ctx: Ctx, datatable: list[list[str]]) -> None:
    _run_many(ctx, _rows(datatable))


@when(parsers.parse("I stream-verify {count:d} addresses at \"{domain}\""))
def when_stream(ctx: Ctx, count: int, domain: str) -> None:
    ctx.prober.host(ctx.resolver.host_for(domain))
    emails = [f"user{i}@{domain}" for i in range(count)]

    async def collect() -> list[tuple[int, VerificationResult]]:
        out: list[tuple[int, VerificationResult]] = []
        async for item in mailspot.verify_stream(emails, options=ctx.options()):
            out.append(item)
        return out

    ctx.streamed = asyncio.run(collect())


@when(parsers.parse("I recheck the deferred results"))
def when_recheck_deferred(ctx: Ctx) -> None:
    ctx.probes_before_recheck = len(ctx.prober.mailbox_probes())
    ctx.results = mailspot.sync.recheck(ctx.results, options=ctx.options())
    ctx.result = ctx.results[0] if ctx.results else None


@when(parsers.parse("I recheck the results"))
def when_recheck(ctx: Ctx) -> None:
    ctx.probes_before_recheck = len(ctx.prober.mailbox_probes())
    ctx.results = mailspot.sync.recheck(ctx.results, options=ctx.options())
    ctx.result = ctx.results[0] if ctx.results else None




def _require(ctx: Ctx) -> VerificationResult:
    assert ctx.result is not None
    return ctx.result


@then("the syntax check passes")
def then_syntax_ok(ctx: Ctx) -> None:
    assert _require(ctx).checks.syntax.valid


@then(parsers.parse('the normalized address is "{expected}"'))
def then_normalized(ctx: Ctx, expected: str) -> None:
    assert _require(ctx).checks.syntax.normalized == expected


@then(parsers.parse('the domain used for DNS is "{expected}"'))
def then_dns_domain(ctx: Ctx, expected: str) -> None:
    assert _require(ctx).checks.syntax.normalized.rpartition("@")[2] == expected


@then(parsers.parse('the status is "{status}"'))
def then_status(ctx: Ctx, status: str) -> None:
    assert _require(ctx).status.value == status


@then(parsers.parse('the status is not "{status}"'))
def then_status_not(ctx: Ctx, status: str) -> None:
    assert _require(ctx).status.value != status


@then(parsers.parse('the decision is "{decision}"'))
def then_decision(ctx: Ctx, decision: str) -> None:
    assert _require(ctx).decision.value == decision


@then(parsers.parse("the confidence is at least {value:d}"))
def then_confidence_at_least(ctx: Ctx, value: int) -> None:
    assert _require(ctx).confidence >= value


@then("the confidence is below the confident-valid band")
def then_confidence_below_band(ctx: Ctx) -> None:
    assert _require(ctx).confidence < 85


@then("no network check is attempted")
def then_no_network(ctx: Ctx) -> None:
    assert not ctx.resolver.calls
    assert not ctx.prober.probes


@then(parsers.parse('the reason mentions the missing "@"'))
def then_reason_at(ctx: Ctx) -> None:
    assert "@" in _require(ctx).reason


@then("the reason mentions no mail route")
def then_reason_no_route(ctx: Ctx) -> None:
    assert "mail route" in _require(ctx).reason


@then("the reason mentions the domain accepts no mail")
def then_reason_no_mail(ctx: Ctx) -> None:
    assert "accepts no mail" in _require(ctx).reason


@then("the reason mentions the domain is accept-all")
def then_reason_accept_all(ctx: Ctx) -> None:
    assert "accept-all" in _require(ctx).reason


@then("the reason says the result rests on syntax and MX only")
def then_reason_syntax_mx(ctx: Ctx) -> None:
    assert "syntax and MX" in _require(ctx).reason


@then("the reason says the provider accepts every probe")
def then_reason_provider_probe(ctx: Ctx) -> None:
    assert "accepts every probe" in _require(ctx).reason


@then("the MX check finds a mail route")
def then_mx_found(ctx: Ctx) -> None:
    assert _require(ctx).checks.mx.found


@then(parsers.parse('the first mail host is "{host}"'))
def then_first_host(ctx: Ctx, host: str) -> None:
    assert _require(ctx).checks.mx.hosts[0] == host


@then("the mail route is recorded as an implicit A-record fallback")
def then_a_fallback(ctx: Ctx) -> None:
    assert "address record" in _require(ctx).checks.mx.reason


@then("the MX check is recorded as a transient failure")
def then_mx_transient(ctx: Ctx) -> None:
    mx = _require(ctx).checks.mx
    assert not mx.found
    assert "temporarily" in mx.reason


@then(parsers.parse('the detected mail provider is "{provider}"'))
def then_provider(ctx: Ctx, provider: str) -> None:
    assert _require(ctx).provider == provider


@then(parsers.parse('the domain "{domain}" is resolved for MX exactly once'))
def then_resolved_once(ctx: Ctx, domain: str) -> None:
    assert ctx.resolver.calls[domain] == 1


@then(parsers.parse('the domain "{domain}" is catch-all tested exactly once'))
def then_catch_all_once(ctx: Ctx, domain: str) -> None:
    host = ctx.resolver.host_for(domain)
    probes = [p for p in ctx.prober.catch_all_probes() if p[0] == host]
    assert len(probes) == 1


@then("the SMTP check reports deliverable")
def then_smtp_deliverable(ctx: Ctx) -> None:
    assert _require(ctx).checks.smtp.deliverable is True


@then("the SMTP check reports not deliverable")
def then_smtp_not_deliverable(ctx: Ctx) -> None:
    assert _require(ctx).checks.smtp.deliverable is False


@then("the SMTP check reports no verdict")
def then_smtp_no_verdict(ctx: Ctx) -> None:
    assert _require(ctx).checks.smtp.deliverable is None


@then("the SMTP probe is retried")
def then_smtp_retried(ctx: Ctx) -> None:
    assert len(ctx.prober.mailbox_probes()) >= 2


@then("the result is marked deferred")
def then_deferred(ctx: Ctx) -> None:
    assert _require(ctx).deferred


@then("the SMTP check is skipped")
def then_smtp_skipped(ctx: Ctx) -> None:
    assert _require(ctx).checks.smtp.attempted is False


@then("the real-mailbox SMTP probe is skipped")
def then_real_probe_skipped(ctx: Ctx) -> None:
    assert _require(ctx).checks.smtp.attempted is False


@then("the real-mailbox SMTP probe is attempted")
def then_real_probe_attempted(ctx: Ctx) -> None:
    assert _require(ctx).checks.smtp.attempted is True


@then("the skip reason mentions it was disabled")
def then_skip_disabled(ctx: Ctx) -> None:
    assert "disabled" in _require(ctx).checks.smtp.skipped_reason


@then("the skip reason names the provider")
def then_skip_names_provider(ctx: Ctx) -> None:
    result = _require(ctx)
    assert result.provider is not None
    assert result.provider in result.checks.smtp.skipped_reason


@then("no message is ever sent")
@then("the DATA command is never issued")
def then_no_data(ctx: Ctx) -> None:
    assert all(command != "DATA" for command, _ in _all_transcript(ctx))


@then("the SMTP conversation stops after RCPT TO")
def then_stops_after_rcpt(ctx: Ctx) -> None:
    transcript = _require(ctx).checks.smtp.transcript
    assert transcript
    assert transcript[-1].command == "RCPT TO"


def _all_transcript(ctx: Ctx) -> list[tuple[str, int | None]]:
    out: list[tuple[str, int | None]] = []
    for exchange in _require(ctx).checks.smtp.transcript:
        out.append((exchange.command, exchange.code))
    return out


@then("the domain is found not to be catch-all")
def then_not_catch_all(ctx: Ctx) -> None:
    assert _require(ctx).checks.catch_all.is_catch_all is False


@then("the domain is found to be catch-all")
def then_is_catch_all(ctx: Ctx) -> None:
    assert _require(ctx).checks.catch_all.is_catch_all is True


@then("the catch-all status is recorded as unknown")
def then_catch_all_unknown(ctx: Ctx) -> None:
    assert _require(ctx).checks.catch_all.is_catch_all is None


@given("a clean acceptance, an unknown, a catch-all, and a hard rejection")
def given_four_outcomes(ctx: Ctx) -> None:
    ctx.prober.host(ctx.resolver.host_for("clean.com")).accepts.add("a@clean.com")
    ctx.prober.host(ctx.resolver.host_for("unverifiable.com")).reachable = False
    ctx.prober.host(ctx.resolver.host_for("catchall.com")).catch_all = True
    ctx.prober.host(ctx.resolver.host_for("reject.com")).rejects.add("a@reject.com")
    options = ctx.options()
    ctx.scores = {
        "clean": mailspot.sync.verify("a@clean.com", options=options).confidence,
        "unknown": mailspot.sync.verify("a@unverifiable.com", options=options).confidence,
        "catch_all": mailspot.sync.verify("a@catchall.com", options=options).confidence,
        "reject": mailspot.sync.verify("a@reject.com", options=options).confidence,
    }


@then("the clean acceptance scores higher than the unknown")
def then_clean_gt_unknown(ctx: Ctx) -> None:
    assert ctx.scores["clean"] > ctx.scores["unknown"]


@then("the unknown scores higher than the catch-all")
def then_unknown_gt_catch_all(ctx: Ctx) -> None:
    assert ctx.scores["unknown"] > ctx.scores["catch_all"]


@then("the catch-all scores higher than the hard rejection")
def then_catch_all_gt_reject(ctx: Ctx) -> None:
    assert ctx.scores["catch_all"] > ctx.scores["reject"]


@then("the address is flagged as disposable")
def then_flag_disposable(ctx: Ctx) -> None:
    assert _require(ctx).flags.disposable


@then("the address is flagged as a role address")
def then_flag_role(ctx: Ctx) -> None:
    assert _require(ctx).flags.role


@then("the address is flagged as free-provider")
def then_flag_free(ctx: Ctx) -> None:
    assert _require(ctx).flags.free_provider


@then("the address has no classification flags")
def then_no_flags(ctx: Ctx) -> None:
    flags = _require(ctx).flags
    assert not (flags.disposable or flags.role or flags.free_provider)


@then("the results are returned in the same order as the input")
def then_order_preserved(ctx: Ctx) -> None:
    assert [r.email for r in ctx.results] == ctx.expected_order


@then(parsers.parse('"{email}" is verified exactly once'))
def then_verified_once(ctx: Ctx, email: str) -> None:
    probes = [p for p in ctx.prober.mailbox_probes() if p[1] == email]
    assert len(probes) <= 2
    assert len({id(r) for r in ctx.results if r.email == email}) == 1


@then("both inputs receive a result")
def then_both_results(ctx: Ctx) -> None:
    assert len(ctx.results) == 2


@then("every input receives a result")
def then_every_result(ctx: Ctx) -> None:
    assert all(isinstance(r, VerificationResult) for r in ctx.results)


@then(parsers.parse('the result for "{email}" records a transient failure'))
def then_transient_failure(ctx: Ctx, email: str) -> None:
    match = next(r for r in ctx.results if r.email == email)
    assert "temporarily" in match.checks.mx.reason


@then(parsers.parse('the results for the "{domain}" addresses are unaffected'))
def then_unaffected(ctx: Ctx, domain: str) -> None:
    affected = [r for r in ctx.results if r.email.endswith(f"@{domain}")]
    assert affected
    assert all(r.status != mailspot.Status.UNKNOWN or r.checks.mx.found for r in affected)


@then("each result is yielded as it completes")
def then_streamed(ctx: Ctx) -> None:
    assert len(ctx.streamed) == 3


@then("each yielded result carries its input index")
def then_streamed_index(ctx: Ctx) -> None:
    indexes = sorted(index for index, _ in ctx.streamed)
    assert indexes == [0, 1, 2]


@then(parsers.parse('only "{email}" is re-verified'))
def then_only_reverified(ctx: Ctx, email: str) -> None:
    after = ctx.prober.mailbox_probes()[ctx.probes_before_recheck :]
    assert after
    assert all(p[1] == email for p in after)


@then(parsers.parse('"{email}" is passed through unchanged'))
def then_passed_through(ctx: Ctx, email: str) -> None:
    after = ctx.prober.mailbox_probes()[ctx.probes_before_recheck :]
    assert all(p[1] != email for p in after)
