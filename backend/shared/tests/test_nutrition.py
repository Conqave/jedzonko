from decimal import Decimal

import pytest

from shared.measurement import Quantity
from shared.measurement_units import find_measurement_unit
from shared.nutrition import (
    CountedKcal,
    InvalidNutritionFactsError,
    NutritionFacts,
    UncountedReason,
    count_kcal,
)

FLOUR = NutritionFacts(kcal_per_100g=Decimal("364"), grams_per_piece=None, grams_per_ml=None)
EGG = NutritionFacts(kcal_per_100g=Decimal("143"), grams_per_piece=Decimal("60"), grams_per_ml=None)
MILK = NutritionFacts(
    kcal_per_100g=Decimal("64"), grams_per_piece=None, grams_per_ml=Decimal("1.03")
)
WITHOUT_CALORIES = NutritionFacts(
    kcal_per_100g=None, grams_per_piece=Decimal("60"), grams_per_ml=Decimal("1")
)


def _quantity(amount: str, unit_code: str) -> Quantity:
    unit = find_measurement_unit(unit_code)
    assert unit is not None
    return Quantity(amount=Decimal(amount), unit=unit)


def test_grams_count_exactly_against_calories_per_100_g() -> None:
    flour = _quantity("250", "g")

    assert count_kcal(flour, FLOUR) == CountedKcal(kcal=Decimal("910"), is_estimate=False)


def test_kilograms_convert_to_grams() -> None:
    flour = _quantity("1.5", "kg")

    assert count_kcal(flour, FLOUR) == CountedKcal(kcal=Decimal("5460"), is_estimate=False)


def test_zero_calories_count_as_zero() -> None:
    salt = NutritionFacts(kcal_per_100g=Decimal("0"), grams_per_piece=None, grams_per_ml=None)
    pinch = _quantity("5", "g")

    assert count_kcal(pinch, salt) == CountedKcal(kcal=Decimal("0"), is_estimate=False)


def test_pieces_are_estimated_through_the_piece_weight() -> None:
    eggs = _quantity("2", "szt")

    assert count_kcal(eggs, EGG) == CountedKcal(kcal=Decimal("171.6"), is_estimate=True)


@pytest.mark.parametrize(("amount", "unit_code"), [("500", "ml"), ("0.5", "l")])
def test_volume_is_estimated_through_the_density(amount: str, unit_code: str) -> None:
    milk = _quantity(amount, unit_code)

    assert count_kcal(milk, MILK) == CountedKcal(kcal=Decimal("329.6"), is_estimate=True)


def test_pieces_without_a_piece_weight_are_not_counted() -> None:
    lemons = _quantity("2", "szt")

    assert count_kcal(lemons, MILK) is UncountedReason.NO_PIECE_WEIGHT


def test_volume_without_a_density_is_not_counted() -> None:
    water = _quantity("200", "ml")

    assert count_kcal(water, EGG) is UncountedReason.NO_DENSITY


def test_packages_are_not_counted_even_with_a_piece_weight() -> None:
    package = _quantity("1", "opak")

    assert count_kcal(package, EGG) is UncountedReason.NO_PACKAGE_WEIGHT


@pytest.mark.parametrize("unit_code", ["g", "ml", "szt"])
def test_a_tag_without_calories_is_not_counted(unit_code: str) -> None:
    amount = _quantity("1", unit_code)

    assert count_kcal(amount, WITHOUT_CALORIES) is UncountedReason.NO_CALORIES


def test_an_untagged_line_is_not_counted() -> None:
    amount = _quantity("100", "g")

    assert count_kcal(amount, None) is UncountedReason.NO_CALORIES


def test_a_line_without_an_amount_is_not_counted() -> None:
    assert count_kcal(None, FLOUR) is UncountedReason.NO_AMOUNT


@pytest.mark.parametrize(
    ("kcal", "piece", "density"),
    [("-1", None, None), (None, "0", None), (None, None, "0"), (None, None, "-0.5")],
)
def test_impossible_facts_are_refused(
    kcal: str | None, piece: str | None, density: str | None
) -> None:
    with pytest.raises(InvalidNutritionFactsError):
        NutritionFacts(
            kcal_per_100g=None if kcal is None else Decimal(kcal),
            grams_per_piece=None if piece is None else Decimal(piece),
            grams_per_ml=None if density is None else Decimal(density),
        )
