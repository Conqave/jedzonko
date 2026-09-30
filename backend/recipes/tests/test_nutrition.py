from decimal import Decimal

from recipes.domain.models import RecipeRequirement
from recipes.domain.nutrition import UncountedIngredient, summarize_nutrition
from recipes.tests.factories import (
    EGGS,
    FLOUR,
    GRAM,
    KILOGRAM,
    MILK,
    MILLILITRE,
    SUGAR,
    make_requirement,
)
from shared.nutrition import UncountedReason

KCAL = {FLOUR: Decimal("364"), SUGAR: Decimal("400"), MILK: Decimal("64")}


def test_mass_lines_add_up_and_split_into_servings() -> None:
    requirements = [
        make_requirement("mąka", "250", GRAM, FLOUR),
        make_requirement("cukier", "0.1", KILOGRAM, SUGAR),
    ]

    nutrition = summarize_nutrition(requirements, KCAL, 4)

    assert nutrition.total_kcal == Decimal("1310")
    assert nutrition.kcal_per_serving == Decimal("327.5")
    assert nutrition.uncounted_ingredients == ()


def test_lines_that_cannot_be_counted_are_listed_with_their_reason() -> None:
    requirements = [
        make_requirement("mąka", "100", GRAM, FLOUR),
        make_requirement("mleko", "200", MILLILITRE, MILK),
        make_requirement("jajka", "120", GRAM, EGGS),
        make_requirement("szafran", "1", GRAM, None),
        RecipeRequirement(name="sól", ingredient_id=None, quantity=None),
    ]

    nutrition = summarize_nutrition(requirements, KCAL, 2)

    assert nutrition.total_kcal == Decimal("364")
    assert nutrition.kcal_per_serving == Decimal("182")
    assert nutrition.uncounted_ingredients == (
        UncountedIngredient(name="mleko", reason=UncountedReason.NOT_BY_MASS),
        UncountedIngredient(name="jajka", reason=UncountedReason.NO_CALORIES),
        UncountedIngredient(name="szafran", reason=UncountedReason.NO_CALORIES),
        UncountedIngredient(name="sól", reason=UncountedReason.NO_AMOUNT),
    )


def test_unknown_servings_give_only_the_total() -> None:
    requirements = [make_requirement("mąka", "100", GRAM, FLOUR)]

    nutrition = summarize_nutrition(requirements, KCAL, None)

    assert nutrition.total_kcal == Decimal("364")
    assert nutrition.kcal_per_serving is None


def test_a_recipe_without_counted_lines_totals_zero() -> None:
    nutrition = summarize_nutrition([], KCAL, 2)

    assert nutrition.total_kcal == Decimal("0")
    assert nutrition.kcal_per_serving == Decimal("0")
