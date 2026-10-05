from __future__ import annotations

import abc
from collections.abc import Mapping, Sequence
from fnmatch import fnmatch
from functools import cache

import yaml

from .resources import read_text


class EmailProvider(abc.ABC):
    name: str | None = None
    verifiable: bool = True
    catch_all_prone: bool = False
    notes: str = ""

    @abc.abstractmethod
    def matches(self, domain: str, hosts: Sequence[str]) -> bool: ...

    def canonical_local(self, local: str) -> str:
        return local

    def canonical_domain(self, domain: str) -> str:
        return domain


class DefaultProvider(EmailProvider):
    name = None
    verifiable = True
    catch_all_prone = False

    def matches(self, domain: str, hosts: Sequence[str]) -> bool:
        return True


class ConfiguredProvider(EmailProvider):
    def __init__(
        self,
        name: str,
        *,
        domains: Sequence[str] = (),
        mx_patterns: Sequence[str] = (),
        verifiable: bool = True,
        catch_all_prone: bool = False,
        notes: str = "",
        ignore_dots: bool = False,
        strip_plus: bool = False,
        domain_aliases: Mapping[str, str] | None = None,
    ) -> None:
        self.name = name
        self.verifiable = verifiable
        self.catch_all_prone = catch_all_prone
        self.notes = notes
        self._domains = frozenset(d.lower() for d in domains)
        self._mx_patterns = tuple(p.lower() for p in mx_patterns)
        self._ignore_dots = ignore_dots
        self._strip_plus = strip_plus
        self._domain_aliases = {k.lower(): v.lower() for k, v in (domain_aliases or {}).items()}

    def matches(self, domain: str, hosts: Sequence[str]) -> bool:
        if domain in self._domains:
            return True
        return any(
            fnmatch(host.lower().rstrip("."), pattern)
            for host in hosts
            for pattern in self._mx_patterns
        )

    def canonical_local(self, local: str) -> str:
        result = local
        if self._ignore_dots:
            result = result.replace(".", "")
        if self._strip_plus:
            result = result.split("+", 1)[0]
        return result

    def canonical_domain(self, domain: str) -> str:
        return self._domain_aliases.get(domain, domain)

    @classmethod
    def from_config(cls, entry: Mapping[str, object]) -> ConfiguredProvider:
        canonical = entry.get("canonical") or {}
        if not isinstance(canonical, Mapping):
            canonical = {}
        return cls(
            name=str(entry["name"]),
            domains=_as_str_list(entry.get("domains")),
            mx_patterns=_as_str_list(entry.get("mx_patterns")),
            verifiable=bool(entry.get("verifiable", True)),
            catch_all_prone=bool(entry.get("catch_all_prone", False)),
            notes=str(entry.get("notes", "")),
            ignore_dots=bool(canonical.get("ignore_dots", False)),
            strip_plus=bool(canonical.get("strip_plus", False)),
            domain_aliases=canonical.get("domain_aliases"),
        )


class ProviderRegistry:
    def __init__(self, providers: Sequence[EmailProvider]) -> None:
        self._providers = tuple(providers)
        self._default = DefaultProvider()

    def resolve(self, domain: str, hosts: Sequence[str] = ()) -> EmailProvider:
        target = domain.lower().rstrip(".")
        normalized_hosts = [h.rstrip(".") for h in hosts]
        for provider in self._providers:
            if provider.matches(target, normalized_hosts):
                return provider
        return self._default

    @classmethod
    def load(cls, overrides: Sequence[EmailProvider] = ()) -> ProviderRegistry:
        return cls((*overrides, *_builtin_providers()))


def _as_str_list(value: object) -> list[str]:
    if isinstance(value, Sequence) and not isinstance(value, str | bytes):
        return [str(item) for item in value]
    return []


@cache
def _builtin_providers() -> tuple[ConfiguredProvider, ...]:
    data = yaml.safe_load(read_text("providers.yaml")) or {}
    entries = data.get("providers", [])
    return tuple(ConfiguredProvider.from_config(entry) for entry in entries)


@cache
def default_registry() -> ProviderRegistry:
    return ProviderRegistry.load()
