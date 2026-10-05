"""The result types and the enums that make up a verdict.

Both result types are pydantic models, so they serialize to JSON and validate
themselves. They carry the evidence behind the headline, not just the headline.
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class Status(StrEnum):
    VALID = "valid"
    INVALID = "invalid"
    RISKY = "risky"
    UNKNOWN = "unknown"


class Decision(StrEnum):
    SEND = "send"
    VERIFY_FIRST = "verify_first"
    SKIP = "skip"
    UNKNOWN = "unknown"


class FinderMethod(StrEnum):
    PATTERN_DETECTED = "pattern_detected"
    PERMUTATION = "permutation"


class SyntaxCheck(BaseModel):
    valid: bool
    normalized: str = ""
    canonical: str = ""
    reason: str = ""


class MxCheck(BaseModel):
    found: bool = False
    hosts: list[str] = Field(default_factory=list)
    provider: str | None = None
    null_mx: bool = False
    reason: str = ""


class SmtpExchange(BaseModel):
    command: str
    code: int | None = None


class SmtpCheck(BaseModel):
    attempted: bool = False
    deliverable: bool | None = None
    code: int | None = None
    reason: str = ""
    skipped_reason: str = ""
    transcript: list[SmtpExchange] = Field(default_factory=list)


class CatchAllCheck(BaseModel):
    tested: bool = False
    is_catch_all: bool | None = None


class Flags(BaseModel):
    disposable: bool = False
    role: bool = False
    free_provider: bool = False


class Checks(BaseModel):
    syntax: SyntaxCheck
    mx: MxCheck = Field(default_factory=MxCheck)
    smtp: SmtpCheck = Field(default_factory=SmtpCheck)
    catch_all: CatchAllCheck = Field(default_factory=CatchAllCheck)


class VerificationResult(BaseModel):
    email: str
    canonical: str = ""
    status: Status
    decision: Decision
    confidence: int = 0
    provider: str | None = None
    deferred: bool = False
    suggestion: str | None = None
    checks: Checks
    flags: Flags = Field(default_factory=Flags)
    reason: str = ""


class Candidate(BaseModel):
    email: str
    pattern: str
    result: VerificationResult


class FinderResult(BaseModel):
    name: str
    domain: str
    best: Candidate | None = None
    candidates: list[Candidate] = Field(default_factory=list)
    detected_pattern: str | None = None
    method: FinderMethod = FinderMethod.PERMUTATION
