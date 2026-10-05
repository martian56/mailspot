from __future__ import annotations

from pytest_bdd import given, parsers, scenarios, then, when

import mailspot
from mailspot.errors import ConfigurationError
from tests.conftest import Ctx

scenarios("email_finder.feature")


@given(parsers.parse('I supply the sample "{name}" is "{email}"'))
def supply_sample(ctx: Ctx, name: str, email: str) -> None:
    ctx.samples.append((name, email))


@when(parsers.parse('I find the email for "{name}" at "{domain}"'))
def find_email(ctx: Ctx, name: str, domain: str) -> None:
    try:
        ctx.finder = mailspot.sync.find(name, domain, samples=ctx.samples, options=ctx.options())
        ctx.find_error = None
    except ConfigurationError as exc:
        ctx.finder = None
        ctx.find_error = exc


@then(parsers.parse('the best candidate is "{email}"'))
def best_is(ctx: Ctx, email: str) -> None:
    assert ctx.finder is not None and ctx.finder.best is not None
    assert ctx.finder.best.email == email


@then(parsers.parse('the method is "{method}"'))
def method_is(ctx: Ctx, method: str) -> None:
    assert ctx.finder is not None
    assert ctx.finder.method.value == method


@then("the best candidate has a high confidence")
def best_high_confidence(ctx: Ctx) -> None:
    assert ctx.finder is not None and ctx.finder.best is not None
    assert ctx.finder.best.result.confidence >= 85


@then(parsers.re(r'the detected pattern is "(?P<pattern>.+)"'))
def detected_pattern_is(ctx: Ctx, pattern: str) -> None:
    assert ctx.finder is not None
    assert ctx.finder.detected_pattern == pattern


@then("the best candidate is marked risky")
def best_risky(ctx: Ctx) -> None:
    assert ctx.finder is not None and ctx.finder.best is not None
    assert ctx.finder.best.result.status is mailspot.Status.RISKY


@then("the result says the domain is accept-all")
def result_accept_all(ctx: Ctx) -> None:
    assert ctx.finder is not None and ctx.finder.best is not None
    assert "accept-all" in ctx.finder.best.result.reason


@then("the find is rejected because the domain has no company pattern")
def find_rejected(ctx: Ctx) -> None:
    assert ctx.find_error is not None


@then(parsers.parse('the candidates include "{email}"'))
def candidates_include(ctx: Ctx, email: str) -> None:
    assert ctx.finder is not None
    assert any(candidate.email == email for candidate in ctx.finder.candidates)


@then("each candidate carries its own verification result")
def candidates_have_results(ctx: Ctx) -> None:
    assert ctx.finder is not None
    assert all(c.result is not None for c in ctx.finder.candidates)
