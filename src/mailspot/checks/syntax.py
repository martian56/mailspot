from __future__ import annotations

import re
from collections.abc import Callable

from ..models import SyntaxCheck
from ..normalize import canonical
from ..providers import ProviderRegistry

_UNQUOTED_LOCAL = re.compile(r"^[A-Za-z0-9!#$%&'*+/=?^_`{|}~.-]+$")
_LABEL = re.compile(r"^[A-Za-z0-9]([A-Za-z0-9-]{0,61}[A-Za-z0-9])?$", re.ASCII)

Rule = Callable[[str, str], str]


def _is_quoted(local: str) -> bool:
    return len(local) >= 2 and local.startswith('"') and local.endswith('"')


def _rule_single_at(local: str, domain: str) -> str:
    if "@" in local and not _is_quoted(local):
        return "address has more than one @"
    return ""


def _rule_local_length(local: str, domain: str) -> str:
    if len(local) > 64:
        return "local part is longer than 64 characters"
    return ""


def _rule_local_charset(local: str, domain: str) -> str:
    if _is_quoted(local):
        return ""
    if local.startswith(".") or local.endswith("."):
        return "local part cannot start or end with a dot"
    if ".." in local:
        return "local part has consecutive dots"
    if not _UNQUOTED_LOCAL.match(local):
        return "local part has characters that are not allowed"
    return ""


def _rule_not_ip_literal(local: str, domain: str) -> str:
    if domain.startswith("["):
        return "IP-literal domains are not supported"
    return ""


def _rule_domain_length(local: str, domain: str) -> str:
    if len(domain) > 253:
        return "domain is longer than 253 characters"
    return ""


def _rule_domain_shape(local: str, domain: str) -> str:
    if "." not in domain:
        return "domain has no dot"
    if domain.startswith(".") or domain.endswith("."):
        return "domain cannot start or end with a dot"
    if ".." in domain:
        return "domain has consecutive dots"
    return ""


_RULES: tuple[Rule, ...] = (
    _rule_single_at,
    _rule_local_length,
    _rule_local_charset,
    _rule_not_ip_literal,
    _rule_domain_length,
    _rule_domain_shape,
)


def _unwrap(email: str) -> str:
    raw = email.strip()
    if raw.startswith("<") and raw.endswith(">"):
        raw = raw[1:-1].strip()
    return raw


def _to_ascii(domain: str) -> str | None:
    cleaned = domain.lower().rstrip(".")
    try:
        ascii_domain = cleaned.encode("idna").decode("ascii")
    except (UnicodeError, UnicodeDecodeError):
        return None
    for label in ascii_domain.split("."):
        if not _LABEL.match(label):
            return None
    return ascii_domain


def check_syntax(email: str, *, registry: ProviderRegistry | None = None) -> SyntaxCheck:
    raw = _unwrap(email)
    if raw.count("@") == 0:
        return SyntaxCheck(valid=False, reason="address has no @")

    local, _, domain = raw.rpartition("@")
    if not local or not domain:
        return SyntaxCheck(valid=False, reason="address needs a local part and a domain")

    for rule in _RULES:
        reason = rule(local, domain)
        if reason:
            return SyntaxCheck(valid=False, reason=reason)

    ascii_domain = _to_ascii(domain)
    if ascii_domain is None:
        return SyntaxCheck(valid=False, reason="domain is not a valid name")

    normalized = f"{local}@{ascii_domain}"
    return SyntaxCheck(
        valid=True,
        normalized=normalized,
        canonical=canonical(normalized, registry=registry),
    )
