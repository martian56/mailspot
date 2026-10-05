from __future__ import annotations

from enum import Enum


class ReplyKind(Enum):
    ACCEPT = "accept"
    REJECT = "reject"
    TEMPORARY = "temporary"
    NONE = "none"


_BY_BUCKET = {2: ReplyKind.ACCEPT, 4: ReplyKind.TEMPORARY, 5: ReplyKind.REJECT}


def classify_code(code: int | None) -> ReplyKind:
    if code is None:
        return ReplyKind.NONE
    return _BY_BUCKET.get(code // 100, ReplyKind.NONE)
