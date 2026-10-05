from __future__ import annotations

from . import sync
from .api import recheck, verify, verify_many, verify_stream
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
    "recheck",
    "suggest",
    "sync",
    "verify",
    "verify_many",
    "verify_stream",
]

__version__ = "0.1.0"
