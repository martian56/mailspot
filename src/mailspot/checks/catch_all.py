from __future__ import annotations

import secrets

from ..infra.ports import SmtpProber
from ..models import CatchAllCheck
from ..options import Options
from .smtp_codes import ReplyKind, classify_code


def _random_recipient(domain: str) -> str:
    return f"mailspot-probe-{secrets.token_hex(12)}@{domain}"


async def check_catch_all(
    host: str,
    domain: str,
    prober: SmtpProber,
    options: Options,
    *,
    proxy: str | None,
) -> CatchAllCheck:
    reply = await prober.probe(
        host,
        _random_recipient(domain),
        helo=options.probe_identity.helo,
        mail_from=options.probe_identity.mail_from,
        timeout=options.smtp_timeout,
        proxy=proxy,
    )
    if not reply.connected:
        return CatchAllCheck(tested=True, is_catch_all=None)

    kind = classify_code(reply.code)
    verdict_by_kind = {
        ReplyKind.ACCEPT: True,
        ReplyKind.REJECT: False,
    }
    return CatchAllCheck(tested=True, is_catch_all=verdict_by_kind.get(kind))
