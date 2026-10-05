"""Exceptions raised to the caller.

An address that cannot be verified is a result, not an exception. These are
reserved for misuse and programmer error.
"""

from __future__ import annotations


class MailspotError(Exception):
    """Base class for everything this library raises."""


class ConfigurationError(MailspotError):
    """Options were built with values that do not make sense together."""
