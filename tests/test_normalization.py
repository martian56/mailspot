from __future__ import annotations

import pytest
from pytest_bdd import parsers, scenarios, then, when

import mailspot

scenarios("normalization.feature")


@pytest.fixture
def box() -> dict[str, object]:
    return {"forms": []}


@when(parsers.parse('I canonicalize "{email}"'))
def canonicalize(box: dict[str, object], email: str) -> None:
    form = mailspot.canonical(email)
    box["form"] = form
    forms = box["forms"]
    assert isinstance(forms, list)
    forms.append(form)


@then(parsers.parse('the canonical form is "{expected}"'))
def check_form(box: dict[str, object], expected: str) -> None:
    assert box["form"] == expected


@then("both canonical forms are equal")
def check_equal(box: dict[str, object]) -> None:
    forms = box["forms"]
    assert isinstance(forms, list)
    assert len(forms) == 2
    assert forms[0] == forms[1]
