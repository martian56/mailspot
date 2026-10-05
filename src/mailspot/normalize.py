from __future__ import annotations

from .providers import ProviderRegistry, default_registry


def split_address(email: str) -> tuple[str, str] | None:
    cleaned = email.strip()
    if cleaned.startswith("<") and cleaned.endswith(">"):
        cleaned = cleaned[1:-1].strip()
    if cleaned.count("@") == 0:
        return None
    local, _, domain = cleaned.rpartition("@")
    if not local or not domain:
        return None
    return local, domain


def canonical(email: str, *, registry: ProviderRegistry | None = None) -> str:
    parts = split_address(email)
    if parts is None:
        return email.strip()
    local, domain = parts
    domain = domain.lower().rstrip(".")
    provider = (registry or default_registry()).resolve(domain)
    local = provider.canonical_local(local)
    domain = provider.canonical_domain(domain)
    return f"{local}@{domain}"
