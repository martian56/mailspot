from __future__ import annotations

from ..models import Flags
from ..options import Options
from ..resources import read_lines


def classify(local: str, domain: str, options: Options) -> Flags:
    domain = domain.lower()
    base_local = local.lower().split("+", 1)[0]

    disposable = read_lines("disposable.txt") | options.extra_disposable
    free = read_lines("free.txt") | options.extra_free
    roles = read_lines("roles.txt") | options.extra_roles

    return Flags(
        disposable=domain in disposable,
        role=base_local in roles,
        free_provider=domain in free,
    )
