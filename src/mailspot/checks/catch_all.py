from __future__ import annotations

import secrets
from dataclasses import dataclass

from ..infra.ports import SmtpProber
from ..models import CatchAllCheck
from ..options import Options
from .smtp_codes import ReplyKind, classify_code


@dataclass(frozen=True)
class CatchAllProbe:
    check: CatchAllCheck
    reachable: bool


def _random_recipient(domain: str) -> str:
    return f"mailspot-probe-{secrets.token_hex(12)}@{domain}"


async def check_catch_all(
    host: str,
    domain: str,
    prober: SmtpProber,
    options: Options,
    *,
    proxy: str | None,
) -> CatchAllProbe:
    reply = await prober.probe(
        host,
        _random_recipient(domain),
        helo=options.probe_identity.helo,
        mail_from=options.probe_identity.mail_from,
        timeout=options.smtp_timeout,
        proxy=proxy,
    )
    if not reply.connected:
        return CatchAllProbe(CatchAllCheck(tested=True, is_catch_all=None), reachable=False)

    verdict_by_kind = {ReplyKind.ACCEPT: True, ReplyKind.REJECT: False}
    is_catch_all = verdict_by_kind.get(classify_code(reply.code))
    return CatchAllProbe(CatchAllCheck(tested=True, is_catch_all=is_catch_all), reachable=True)
