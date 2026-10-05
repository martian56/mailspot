"""mailspot: find and verify work email addresses, with no API keys."""

from __future__ import annotations

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
from .options import Options, ProbeIdentity

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
]

__version__ = "0.1.0"
