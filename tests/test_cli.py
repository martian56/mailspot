from __future__ import annotations

import json
import shlex
from pathlib import Path

import pytest
from pytest_bdd import given, parsers, scenarios, then, when
from typer.testing import CliRunner

from mailspot import cli
from tests.conftest import Ctx

scenarios("cli.feature")


@pytest.fixture(autouse=True)
def work_dir(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    monkeypatch.chdir(tmp_path)
    return tmp_path


def _run(ctx: Ctx, command: str):
    cli.options_factory = ctx.options
    args = shlex.split(command)[1:]
    return CliRunner().invoke(cli.app, args)


@given(parsers.parse('a CSV "{filename}" with an "{column}" column of {count:d} addresses'))
def given_csv(ctx: Ctx, filename: str, column: str, count: int) -> None:
    emails = [f"user{i}@acme.com" for i in range(count)]
    ctx.csv_emails = emails
    lines = [column, *emails]
    Path(filename).write_text("\n".join(lines), encoding="utf-8")


@given("a mail host that answers for their domains")
def given_host_for_csv(ctx: Ctx) -> None:
    for email in ctx.csv_emails:
        ctx.prober.host(ctx.resolver.host_for(email.rpartition("@")[2]))


@when(parsers.parse('I run "{command}"'))
def when_run(ctx: Ctx, command: str) -> None:
    ctx.cli_result = _run(ctx, command)


@when(parsers.parse('I run "{command}" and capture streams separately'))
def when_run_split(ctx: Ctx, command: str) -> None:
    ctx.cli_result = _run(ctx, command)


@then(parsers.parse('the output contains "{text}"'))
def then_output_contains(ctx: Ctx, text: str) -> None:
    assert text in ctx.cli_result.stdout


@then(parsers.parse('the output contains the decision "{decision}"'))
def then_output_decision(ctx: Ctx, decision: str) -> None:
    assert decision in ctx.cli_result.stdout


@then(parsers.parse("the exit code is {code:d}"))
def then_exit_code(ctx: Ctx, code: int) -> None:
    assert ctx.cli_result.exit_code == code


@then("stdout is valid JSON")
def then_stdout_json(ctx: Ctx) -> None:
    json.loads(ctx.cli_result.stdout)


@then(parsers.parse('the JSON has a "{field}" field'))
def then_json_field(ctx: Ctx, field: str) -> None:
    assert field in json.loads(ctx.cli_result.stdout)


@then("the output reports the address as invalid")
def then_reports_invalid(ctx: Ctx) -> None:
    assert "invalid" in ctx.cli_result.stdout


@then("stdout is empty")
def then_stdout_empty(ctx: Ctx) -> None:
    assert ctx.cli_result.stdout.strip() == ""


@then(parsers.parse('"{filename}" has a row per input'))
def then_rows_per_input(ctx: Ctx, filename: str) -> None:
    lines = [line for line in Path(filename).read_text(encoding="utf-8").splitlines() if line]
    assert len(lines) == len(ctx.csv_emails) + 1


@then(parsers.parse('"{filename}" has the columns "{columns}"'))
def then_has_columns(ctx: Ctx, filename: str, columns: str) -> None:
    header = Path(filename).read_text(encoding="utf-8").splitlines()[0]
    present = {part.strip() for part in header.split(",")}
    for column in columns.split(","):
        assert column.strip() in present


@then("the error mentions the file could not be read")
def then_error_file(ctx: Ctx) -> None:
    assert "could not read" in ctx.cli_result.stderr


@then("stdout contains only the JSON")
def then_stdout_only_json(ctx: Ctx) -> None:
    json.loads(ctx.cli_result.stdout)


@then("any progress output is on stderr")
def then_progress_stderr(ctx: Ctx) -> None:
    assert "{" not in ctx.cli_result.stderr
