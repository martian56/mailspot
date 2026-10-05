from __future__ import annotations

import pytest
from pytest_bdd import parsers, scenarios, then, when

import mailspot

scenarios("typo_suggestion.feature")


@pytest.fixture
def box() -> dict[str, object]:
    return {}


@when(parsers.parse('I ask for a suggestion for "{email}"'))
def ask_suggestion(box: dict[str, object], email: str) -> None:
    box["suggestion"] = mailspot.suggest(email)


@when(parsers.parse('I verify "{email}"'))
def verify_for_suggestion(box: dict[str, object], email: str) -> None:
    box["suggestion"] = mailspot.suggest(email)


@then(parsers.parse('the suggestion is "{expected}"'))
def check_suggestion(box: dict[str, object], expected: str) -> None:
    assert box["suggestion"] == expected


@then("there is no suggestion")
def check_no_suggestion(box: dict[str, object]) -> None:
    assert box["suggestion"] is None


@then(parsers.parse('the result suggests "{expected}"'))
def check_result_suggestion(box: dict[str, object], expected: str) -> None:
    assert box["suggestion"] == expected
