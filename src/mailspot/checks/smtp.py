from __future__ import annotations

from ..infra.ports import Clock, SmtpProber, SmtpReply
from ..models import SmtpCheck, SmtpExchange
from ..options import Options
from .smtp_codes import ReplyKind, classify_code


def _transcript(reply: SmtpReply) -> list[SmtpExchange]:
    return [SmtpExchange(command=command, code=code) for command, code in reply.transcript]


async def probe_mailbox(
    host: str,
    recipient: str,
    prober: SmtpProber,
    clock: Clock,
    options: Options,
    *,
    proxy: str | None,
    backoff: float = 2.0,
) -> tuple[SmtpCheck, bool]:
    attempts = options.smtp_retries + 1
    reply = SmtpReply(connected=False)

    for attempt in range(attempts):
        reply = await prober.probe(
            host,
            recipient,
            helo=options.probe_identity.helo,
            mail_from=options.probe_identity.mail_from,
            timeout=options.smtp_timeout,
            proxy=proxy,
        )
        if not reply.connected:
            return SmtpCheck(
                attempted=True,
                reason=reply.error or "could not reach the mail host",
                transcript=_transcript(reply),
            ), False

        kind = classify_code(reply.code)
        if kind is ReplyKind.ACCEPT:
            return SmtpCheck(
                attempted=True,
                deliverable=True,
                code=reply.code,
                reason="the server accepted the mailbox",
                transcript=_transcript(reply),
            ), False
        if kind is ReplyKind.REJECT:
            return SmtpCheck(
                attempted=True,
                deliverable=False,
                code=reply.code,
                reason="the server rejected the mailbox",
                transcript=_transcript(reply),
            ), False
        if kind is ReplyKind.TEMPORARY and attempt < attempts - 1:
            await clock.sleep(backoff)
            continue
        break

    if classify_code(reply.code) is ReplyKind.TEMPORARY:
        return SmtpCheck(
            attempted=True,
            code=reply.code,
            reason="temporary response, deferred for a later re-check",
            transcript=_transcript(reply),
        ), True

    return SmtpCheck(
        attempted=True,
        code=reply.code,
        reason="no definitive response from the server",
        transcript=_transcript(reply),
    ), False
