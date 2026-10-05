from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from .evidence import Evidence
from .models import Decision, Status

HIGH_CONFIDENCE = 85
PARTIAL_EVIDENCE_CAP = 52
CATCH_ALL_CAP = 42
DISPOSABLE_CAP = 20


@dataclass(frozen=True)
class Score:
    status: Status
    confidence: int
    decision: Decision
    reason: str


StatusRule = Callable[[Evidence], tuple[Status, str] | None]


def _invalid_syntax(e: Evidence) -> tuple[Status, str] | None:
    if not e.syntax.valid:
        return Status.INVALID, e.syntax.reason
    return None


def _invalid_domain(e: Evidence) -> tuple[Status, str] | None:
    answer = e.mx_answer
    if answer is not None and answer.transient_error:
        return None
    if e.mx.null_mx:
        return Status.INVALID, "the domain accepts no mail"
    if answer is not None and not answer.domain_exists:
        return Status.INVALID, "the domain does not exist"
    if not e.mx.found:
        return Status.INVALID, "the domain has no mail route"
    return None


def _rejected_mailbox(e: Evidence) -> tuple[Status, str] | None:
    if e.smtp_rejected:
        return Status.INVALID, "the server rejected the mailbox"
    return None


def _confirmed_valid(e: Evidence) -> tuple[Status, str] | None:
    if e.smtp_accepted and e.confirmed_not_catch_all and e.provider_verifiable:
        return Status.VALID, "the server accepted the mailbox on a domain that is not accept-all"
    return None


def _catch_all(e: Evidence) -> tuple[Status, str] | None:
    if e.catch_all.is_catch_all is True:
        return Status.RISKY, "the domain is accept-all, so the mailbox cannot be confirmed"
    return None


def _unverifiable_provider(e: Evidence) -> tuple[Status, str] | None:
    if not e.provider_verifiable:
        return Status.RISKY, "the provider accepts every probe, so the mailbox cannot be confirmed"
    return None


def _disposable(e: Evidence) -> tuple[Status, str] | None:
    if e.flags.disposable:
        return Status.RISKY, "the domain is a disposable mail service"
    return None


def _accepted_but_unproven(e: Evidence) -> tuple[Status, str] | None:
    if e.smtp_accepted:
        return Status.RISKY, "the server accepted the mailbox, but the domain is not proven safe"
    return None


_STATUS_RULES: tuple[StatusRule, ...] = (
    _invalid_syntax,
    _invalid_domain,
    _rejected_mailbox,
    _confirmed_valid,
    _catch_all,
    _unverifiable_provider,
    _disposable,
    _accepted_but_unproven,
)


def _resolve_status(e: Evidence) -> tuple[Status, str]:
    for rule in _STATUS_RULES:
        outcome = rule(e)
        if outcome is not None:
            return outcome
    return Status.UNKNOWN, "not enough evidence to confirm or reject the mailbox"


def _confidence(e: Evidence, status: Status) -> int:
    if status is Status.INVALID:
        return 2 if e.syntax.valid else 0

    value = 10
    if e.mx.found:
        value += 30
    if e.smtp_accepted:
        value += 55

    inconclusive = e.smtp.deliverable is None
    if not e.provider_verifiable or inconclusive:
        value = min(value, PARTIAL_EVIDENCE_CAP)
    if e.catch_all.is_catch_all is True:
        value = min(value, CATCH_ALL_CAP) - 5
    if e.flags.disposable:
        value = min(value, DISPOSABLE_CAP)
    if e.flags.role:
        value -= 10

    return max(0, min(value, 97))


def _decide(e: Evidence, status: Status, confidence: int) -> Decision:
    if status is Status.INVALID or e.flags.disposable:
        return Decision.SKIP
    if status is Status.UNKNOWN:
        return Decision.UNKNOWN
    if status is Status.RISKY:
        return Decision.VERIFY_FIRST
    if confidence >= HIGH_CONFIDENCE and not e.flags.role:
        return Decision.SEND
    return Decision.VERIFY_FIRST


def score(e: Evidence) -> Score:
    status, reason = _resolve_status(e)
    confidence = _confidence(e, status)
    decision = _decide(e, status, confidence)
    return Score(status=status, confidence=confidence, decision=decision, reason=reason)
