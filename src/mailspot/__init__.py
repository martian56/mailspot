from __future__ import annotations

from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as _package_version

from . import sync
from .api import find, recheck, verify, verify_many, verify_stream
from .errors import ConfigurationError, MailspotError
from .models import (
    Candidate,
    Checks,
    Decision,
    FinderMethod,
    FinderResult,
    Flags,
    Status,
    VerificationResult,
)
from .normalize import canonical
from .options import Options, ProbeIdentity
from .suggest import suggest

__all__ = [
    "Candidate",
    "Checks",
    "ConfigurationError",
    "Decision",
    "FinderMethod",
    "FinderResult",
    "Flags",
    "MailspotError",
    "Options",
    "ProbeIdentity",
    "Status",
    "VerificationResult",
    "canonical",
    "find",
    "recheck",
    "suggest",
    "sync",
    "verify",
    "verify_many",
    "verify_stream",
]

try:
    __version__ = _package_version("mailspot")
except PackageNotFoundError:
    __version__ = "0.0.0"
