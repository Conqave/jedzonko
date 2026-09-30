from decimal import Decimal

import pytest

from shared.item_calories import ItemCalories, SubjectNutrition, TagGap, count_item_calories
from shared.measurement import Quantity
from shared.measurement_units import find_measurement_unit
from shared.nutrition import NutritionFacts, UncountedReason

PASTA = NutritionFacts(kcal_per_100g=Decimal("350"), grams_per_piece=None, grams_per_ml=None)
EGG = NutritionFacts(kcal_per_100g=Decimal("143"), grams_per_piece=Decimal("60"), grams_per_ml=None)


def _quantity(amount: str, unit_code: str) -> Quantity:
    unit = find_measurement_unit(unit_code)
    assert unit is not None
    return Quantity(amount=Decimal(amount), unit=unit)


def test_a_weighed_amount_is_counted_exactly() -> None:
    nutrition = SubjectNutrition(facts=PASTA, package=None)

    calories = count_item_calories(_quantity("0.5", "kg"), nutrition)

    assert calories == ItemCalories(
        kcal=Decimal("1750"),
        kcal_per_100g=Decimal("350"),
        is_estimate=False,
        uncounted_reason=None,
    )


def test_pieces_are_counted_as_an_estimate() -> None:
    nutrition = SubjectNutrition(facts=EGG, package=None)

    calories = count_item_calories(_quantity("10", "szt"), nutrition)

    assert calories.kcal == Decimal("858")
    assert calories.is_estimate is True


def test_packages_are_counted_through_the_product_package() -> None:
    nutrition = SubjectNutrition(facts=PASTA, package=_quantity("500", "g"))

    calories = count_item_calories(_quantity("2", "opak"), nutrition)

    assert calories.kcal == Decimal("3500")
    assert calories.is_estimate is False


def test_a_package_does_not_change_other_units() -> None:
    nutrition = SubjectNutrition(facts=PASTA, package=_quantity("500", "g"))

    calories = count_item_calories(_quantity("200", "g"), nutrition)

    assert calories.kcal == Decimal("700")


def test_packages_without_a_package_size_are_not_counted() -> None:
    nutrition = SubjectNutrition(facts=PASTA, package=None)

    calories = count_item_calories(_quantity("2", "opak"), nutrition)

    assert calories.kcal is None
    assert calories.uncounted_reason is UncountedReason.NO_PACKAGE_WEIGHT
    assert calories.kcal_per_100g == Decimal("350")


@pytest.mark.parametrize("gap", list(TagGap))
def test_a_subject_without_a_single_tag_says_why(gap: TagGap) -> None:
    nutrition = SubjectNutrition(facts=gap, package=None)

    calories = count_item_calories(_quantity("1", "kg"), nutrition)

    assert calories == ItemCalories(
        kcal=None, kcal_per_100g=None, is_estimate=False, uncounted_reason=gap
    )


def test_a_missing_amount_is_not_counted() -> None:
    nutrition = SubjectNutrition(facts=PASTA, package=None)

    calories = count_item_calories(None, nutrition)

    assert calories.uncounted_reason is UncountedReason.NO_AMOUNT


def test_calories_are_either_counted_or_explained() -> None:
    with pytest.raises(AssertionError):
        ItemCalories(kcal=None, kcal_per_100g=None, is_estimate=False, uncounted_reason=None)
    with pytest.raises(AssertionError):
        ItemCalories(
            kcal=Decimal("1"),
            kcal_per_100g=None,
            is_estimate=False,
            uncounted_reason=TagGap.NO_TAG,
        )


def test_only_counted_calories_are_estimates() -> None:
    with pytest.raises(AssertionError):
        ItemCalories(
            kcal=None, kcal_per_100g=None, is_estimate=True, uncounted_reason=TagGap.NO_TAG
        )
