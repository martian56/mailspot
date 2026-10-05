from __future__ import annotations

import sys
import urllib.request
from pathlib import Path

DATA = Path(__file__).resolve().parent.parent / "src" / "mailspot" / "data"

DISPOSABLE_SOURCES = (
    "https://raw.githubusercontent.com/disposable-email-domains/"
    "disposable-email-domains/master/disposable_email_blocklist.conf",
)

TIMEOUT = 30


def fetch(url: str) -> list[str]:
    with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
        body = response.read().decode("utf-8")
    return [line.strip().lower() for line in body.splitlines() if line.strip()]


def load(path: Path) -> set[str]:
    if not path.exists():
        return set()
    return {
        line.strip().lower()
        for line in path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.startswith("#")
    }


def write(path: Path, domains: set[str]) -> None:
    path.write_text("\n".join(sorted(domains)) + "\n", encoding="utf-8")


def update_disposable() -> int:
    path = DATA / "disposable.txt"
    before = load(path)
    fetched: set[str] = set()
    for url in DISPOSABLE_SOURCES:
        fetched.update(fetch(url))
    combined = before | fetched
    write(path, combined)
    return len(combined) - len(before)


def main() -> int:
    try:
        added = update_disposable()
    except OSError as exc:
        print(f"could not update lists: {exc}", file=sys.stderr)
        return 1
    print(f"disposable list updated, {added} new domains")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
