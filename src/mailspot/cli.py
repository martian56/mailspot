from __future__ import annotations

import csv
import sys
from collections.abc import Callable
from pathlib import Path

import typer

from . import sync
from .models import FinderResult, VerificationResult
from .options import Options

app = typer.Typer(add_completion=False, help="Find and verify work email addresses.")
bulk_app = typer.Typer(help="Verify or find in bulk from a CSV.")
app.add_typer(bulk_app, name="bulk")

options_factory: Callable[[], Options] = Options

_RESULT_COLUMNS = ["email", "status", "decision", "confidence", "reason"]


def _options(*, no_smtp: bool, no_catch_all: bool, proxy: str | None) -> Options:
    base = options_factory()
    return base.with_(
        smtp_enabled=base.smtp_enabled and not no_smtp,
        catch_all_enabled=base.catch_all_enabled and not no_catch_all,
        proxy=proxy if proxy is not None else base.proxy,
    )


def _line(result: VerificationResult) -> str:
    return (
        f"{result.email}  {result.status.value}  {result.decision.value}  "
        f"{result.confidence}  {result.reason}"
    )


def _emit(result: VerificationResult, as_json: bool) -> None:
    typer.echo(result.model_dump_json() if as_json else _line(result))


def _progress(message: str) -> None:
    typer.echo(message, err=True)


@app.command()
def verify(
    email: str,
    json_output: bool = typer.Option(False, "--json", help="Emit the full result as JSON."),
    no_smtp: bool = typer.Option(False, "--no-smtp", help="Skip SMTP probing."),
    no_catch_all: bool = typer.Option(False, "--no-catch-all", help="Skip catch-all detection."),
    proxy: str | None = typer.Option(None, "--proxy", help="Route SMTP through this proxy."),
) -> None:
    options = _options(no_smtp=no_smtp, no_catch_all=no_catch_all, proxy=proxy)
    _emit(sync.verify(email, options=options), json_output)


@app.command()
def find(
    name: str = typer.Option(..., "--name"),
    domain: str = typer.Option(..., "--domain"),
    sample: list[str] = typer.Option([], "--sample", help='A known "Name=email" pair.'),
    json_output: bool = typer.Option(False, "--json"),
    no_smtp: bool = typer.Option(False, "--no-smtp"),
    proxy: str | None = typer.Option(None, "--proxy"),
) -> None:
    samples = [_parse_sample(entry) for entry in sample]
    result = sync.find(
        name,
        domain,
        samples=samples,
        options=_options(no_smtp=no_smtp, no_catch_all=False, proxy=proxy),
    )
    _emit_finder(result, json_output)


@app.command()
def suggest(email: str) -> None:
    from .suggest import suggest as suggest_fn

    correction = suggest_fn(email)
    if correction is not None:
        typer.echo(correction)


@app.command()
def canonical(email: str) -> None:
    from .normalize import canonical as canonical_fn

    typer.echo(canonical_fn(email))


@bulk_app.command("verify")
def bulk_verify(
    path: Path,
    column: str = typer.Option("email", "--column"),
    out: Path | None = typer.Option(None, "--out"),
    no_smtp: bool = typer.Option(False, "--no-smtp"),
    proxy: str | None = typer.Option(None, "--proxy"),
) -> None:
    rows = _read_csv(path)
    emails = [row[column] for row in rows]
    results = sync.verify_many(
        emails, options=_options(no_smtp=no_smtp, no_catch_all=False, proxy=proxy)
    )
    _progress(f"verified {len(results)} addresses")
    _write_results(out, rows, results)


@bulk_app.command("find")
def bulk_find(
    path: Path,
    name_column: str = typer.Option("name", "--name-column"),
    domain_column: str = typer.Option("domain", "--domain-column"),
    out: Path | None = typer.Option(None, "--out"),
) -> None:
    rows = _read_csv(path)
    results = [
        sync.find(row[name_column], row[domain_column], options=options_factory()) for row in rows
    ]
    best = [r.best.result if r.best else _missing(r) for r in results]
    _write_results(out, rows, best)


@bulk_app.command("recheck")
def bulk_recheck(path: Path, out: Path | None = typer.Option(None, "--out")) -> None:
    rows = _read_csv(path)
    prior = [_row_to_result(row) for row in rows]
    results = sync.recheck(prior)
    _write_results(out, rows, results)


def _parse_sample(entry: str) -> tuple[str, str]:
    name, _, email = entry.partition("=")
    return name.strip(), email.strip()


def _emit_finder(result: FinderResult, as_json: bool) -> None:
    if as_json:
        typer.echo(result.model_dump_json())
        return
    if result.best is None:
        typer.echo(f"no credible address found for {result.name} at {result.domain}")
        return
    best = result.best
    typer.echo(f"{best.email}  {best.result.confidence}  via {result.method.value}")
    for candidate in result.candidates:
        if candidate.email != best.email:
            typer.echo(f"  tried {candidate.email}  {candidate.result.status.value}")


def _read_csv(path: Path) -> list[dict[str, str]]:
    try:
        text = path.read_text(encoding="utf-8")
    except OSError as exc:
        _progress(f"could not read {path}: {exc}")
        raise typer.Exit(1) from exc
    return list(csv.DictReader(text.splitlines()))


def _write_results(
    out: Path | None,
    rows: list[dict[str, str]],
    results: list[VerificationResult],
) -> None:
    extra = [column for column in rows[0] if column not in _RESULT_COLUMNS] if rows else []
    fieldnames = extra + _RESULT_COLUMNS
    stream = out.open("w", encoding="utf-8", newline="") if out else sys.stdout
    try:
        writer = csv.DictWriter(stream, fieldnames=fieldnames)
        writer.writeheader()
        for row, result in zip(rows, results, strict=False):
            record = {column: row.get(column, "") for column in extra}
            record.update(_result_row(result))
            writer.writerow(record)
    finally:
        if out:
            stream.close()


def _result_row(result: VerificationResult) -> dict[str, str]:
    return {
        "email": result.email,
        "status": result.status.value,
        "decision": result.decision.value,
        "confidence": str(result.confidence),
        "reason": result.reason,
    }


def _row_to_result(row: dict[str, str]) -> VerificationResult:
    from .models import Checks, Decision, Status, SyntaxCheck

    return VerificationResult(
        email=row["email"],
        status=Status(row.get("status", "unknown")),
        decision=Decision(row.get("decision", "unknown")),
        deferred=row.get("decision") == "unknown",
        checks=Checks(syntax=SyntaxCheck(valid=True)),
    )


def _missing(result: FinderResult) -> VerificationResult:
    from .models import Checks, Decision, Status, SyntaxCheck

    return VerificationResult(
        email=f"@{result.domain}",
        status=Status.UNKNOWN,
        decision=Decision.UNKNOWN,
        checks=Checks(syntax=SyntaxCheck(valid=False)),
    )


if __name__ == "__main__":
    app()
