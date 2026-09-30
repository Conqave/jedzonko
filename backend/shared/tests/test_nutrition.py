from decimal import Decimal

import pytest

from shared.measurement import Quantity
from shared.measurement_units import find_measurement_unit
from shared.nutrition import UncountedReason, count_kcal


def _quantity(amount: str, unit_code: str) -> Quantity:
    unit = find_measurement_unit(unit_code)
    assert unit is not None
    return Quantity(amount=Decimal(amount), unit=unit)


def test_grams_count_against_calories_per_100_g() -> None:
    flour = _quantity("250", "g")

    assert count_kcal(flour, Decimal("364")) == Decimal("910")


def test_kilograms_convert_to_grams() -> None:
    potatoes = _quantity("1.5", "kg")

    assert count_kcal(potatoes, Decimal("77")) == Decimal("1155")


def test_zero_calories_count_as_zero() -> None:
    salt = _quantity("5", "g")

    assert count_kcal(salt, Decimal("0")) == Decimal("0")


@pytest.mark.parametrize("unit_code", ["ml", "l", "szt", "opak"])
def test_volume_and_count_are_not_counted(unit_code: str) -> None:
    milk = _quantity("1", unit_code)

    assert count_kcal(milk, Decimal("64")) is UncountedReason.NOT_BY_MASS


def test_a_tag_without_calories_is_not_counted() -> None:
    flour = _quantity("250", "g")

    assert count_kcal(flour, None) is UncountedReason.NO_CALORIES


def test_a_line_without_an_amount_is_not_counted() -> None:
    assert count_kcal(None, Decimal("364")) is UncountedReason.NO_AMOUNT
