from __future__ import annotations

from dataclasses import dataclass

from .infra.ports import MxAnswer
from .models import CatchAllCheck, Flags, MxCheck, SmtpCheck, SyntaxCheck
from .providers import EmailProvider


@dataclass(frozen=True)
class Evidence:
    email: str
    normalized: str
    canonical: str
    suggestion: str | None
    syntax: SyntaxCheck
    flags: Flags
    mx: MxCheck
    mx_answer: MxAnswer | None
    provider: EmailProvider
    catch_all: CatchAllCheck
    smtp: SmtpCheck
    deferred: bool

    @property
    def smtp_accepted(self) -> bool:
        return self.smtp.deliverable is True

    @property
    def smtp_rejected(self) -> bool:
        return self.smtp.deliverable is False

    @property
    def confirmed_not_catch_all(self) -> bool:
        return self.catch_all.is_catch_all is False

    @property
    def provider_verifiable(self) -> bool:
        return self.provider.verifiable
