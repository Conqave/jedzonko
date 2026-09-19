from decimal import Decimal

import pytest

from recipes.application.ports.recipe_source import RecipeSourceContractError
from recipes.infrastructure.providers.ania_gotuje.duration import parse_iso_duration_minutes
from recipes.infrastructure.providers.ania_gotuje.ingredient_line import parse_ingredient_line


@pytest.mark.parametrize(
    ("value", "expected"),
    [
        ("PT0H5M", 5),
        ("PT0H25M", 25),
        ("PT1H0M", 60),
        ("PT1H30M", 90),
        ("PT2H", 120),
        ("PT45M", 45),
        ("P1DT2H", 1560),
        ("PT90S", 1),
    ],
)
def test_parse_iso_duration_minutes(value: str, expected: int) -> None:
    assert parse_iso_duration_minutes(value) == expected


@pytest.mark.parametrize("value", ["5 minut", "", "P", "PT0H5X", "1H"])
def test_parse_iso_duration_rejects_unsupported_values(value: str) -> None:
    with pytest.raises(RecipeSourceContractError):
        parse_iso_duration_minutes(value)


@pytest.mark.parametrize(
    ("line", "name", "amount", "unit_code"),
    [
        (
            "1 pełna szklanka i 2 łyżki mąki pszennej - 230 g",
            "1 pełna szklanka i 2 łyżki mąki pszennej",
            Decimal("230"),
            "g",
        ),
        ("1 szklanka mleka - 250 ml", "1 szklanka mleka", Decimal("250"), "ml"),
        ("2,5 szklanki mąki pszennej - 0,4 kg", "2,5 szklanki mąki pszennej", Decimal("0.4"), "kg"),
    ],
)
def test_parse_ingredient_line_reads_trailing_amount(
    line: str, name: str, amount: Decimal, unit_code: str
) -> None:
    parsed = parse_ingredient_line(line)

    assert parsed.source_text == line
    assert parsed.name == name
    assert parsed.quantity == amount
    assert parsed.unit_code == unit_code


@pytest.mark.parametrize(
    "line",
    [
        "szczypta soli",
        "3 średnie jajka - około 165 g po rozbiciu",
        "niecałe pół szklanki cukru - około 130 g",
        "5 płaskich łyżek surowego kakao - lub mniej",
        "1 kg mielonego twarogu np. z kubełka",
        "1 szklanka mleka - 250 filiżanek",
        "2 łyżeczki proszku do pieczenia",
    ],
)
def test_parse_ingredient_line_keeps_ambiguous_lines_as_text(line: str) -> None:
    parsed = parse_ingredient_line(line)

    assert parsed.quantity is None
    assert parsed.unit_code is None
    assert parsed.name == line
    assert parsed.source_text == line
