from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field

from mailspot.infra.ports import MxAnswer, SmtpReply

_GREYLIST_UNTIL = 2


@dataclass
class HostBehavior:
    reachable: bool = True
    catch_all: bool = False
    accepts: set[str] = field(default_factory=set)
    rejects: set[str] = field(default_factory=set)
    greylisted: set[str] = field(default_factory=set)
    greylist_all: bool = False
    catch_all_probe_unreachable: bool = False

    def reply(self, recipient: str, attempt: int, is_catch_all_probe: bool) -> SmtpReply:
        if not self.reachable:
            return SmtpReply(connected=False, error="connection timed out")
        if is_catch_all_probe and self.catch_all_probe_unreachable:
            return SmtpReply(connected=False, error="connection timed out")
        transcript: list[tuple[str, int | None]] = [
            ("CONNECT", 220),
            ("EHLO", 250),
            ("MAIL FROM", 250),
        ]
        code = self._code(recipient, attempt)
        transcript.append(("RCPT TO", code))
        return SmtpReply(connected=True, code=code, transcript=tuple(transcript))

    def _code(self, recipient: str, attempt: int) -> int:
        greylisted = recipient in self.greylisted or self.greylist_all
        if greylisted and attempt <= _GREYLIST_UNTIL:
            return 451
        if self.catch_all:
            return 250
        if recipient in self.accepts:
            return 250
        if recipient in self.rejects:
            return 550
        return 550


class FakeProber:
    def __init__(self) -> None:
        self._hosts: dict[str, HostBehavior] = {}
        self.probes: list[tuple[str, str]] = []
        self._attempts: Counter[tuple[str, str]] = Counter()

    def host(self, name: str) -> HostBehavior:
        return self._hosts.setdefault(name, HostBehavior())

    def known(self, name: str) -> bool:
        return name in self._hosts

    async def probe(
        self,
        host: str,
        recipient: str,
        *,
        helo: str,
        mail_from: str,
        timeout: float,
        proxy: str | None,
    ) -> SmtpReply:
        self.probes.append((host, recipient))
        self._attempts[(host, recipient)] += 1
        behavior = self._hosts.get(host)
        if behavior is None:
            return SmtpReply(connected=False, error="no such host")
        is_catch_all_probe = recipient.startswith("mailspot-probe-")
        return behavior.reply(recipient, self._attempts[(host, recipient)], is_catch_all_probe)

    def mailbox_probes(self) -> list[tuple[str, str]]:
        return [p for p in self.probes if not p[1].startswith("mailspot-probe-")]

    def catch_all_probes(self) -> list[tuple[str, str]]:
        return [p for p in self.probes if p[1].startswith("mailspot-probe-")]


class FakeResolver:
    def __init__(self) -> None:
        self._answers: dict[str, MxAnswer] = {}
        self.calls: Counter[str] = Counter()

    def set(self, domain: str, answer: MxAnswer) -> None:
        self._answers[domain] = answer

    def host_for(self, domain: str) -> str:
        answer = self._answers.get(domain)
        if answer and answer.hosts:
            return answer.hosts[0]
        return f"mail.{domain}"

    async def resolve_mx(self, domain: str, *, timeout: float) -> MxAnswer:
        self.calls[domain] += 1
        return self._answers.get(domain, MxAnswer(hosts=(f"mail.{domain}",)))


class FakeClock:
    def __init__(self) -> None:
        self._now = 0.0

    def now(self) -> float:
        return self._now

    async def sleep(self, seconds: float) -> None:
        if seconds > 0:
            self._now += seconds


def greylist_threshold() -> int:
    return _GREYLIST_UNTIL
