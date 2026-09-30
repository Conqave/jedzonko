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
    PACKAGE,
    PIECE,
    SUGAR,
    make_requirement,
)
from shared.nutrition import NutritionFacts, UncountedReason


def _facts(
    kcal: str | None, piece: str | None = None, density: str | None = None
) -> NutritionFacts:
    return NutritionFacts(
        kcal_per_100g=None if kcal is None else Decimal(kcal),
        grams_per_piece=None if piece is None else Decimal(piece),
        grams_per_ml=None if density is None else Decimal(density),
    )


FACTS = {
    FLOUR: _facts("364"),
    SUGAR: _facts("400"),
    MILK: _facts("64", density="1.03"),
    EGGS: _facts("143", piece="60"),
}


def test_mass_lines_add_up_exactly_and_split_into_servings() -> None:
    requirements = [
        make_requirement("mąka", "250", GRAM, FLOUR),
        make_requirement("cukier", "0.1", KILOGRAM, SUGAR),
    ]

    nutrition = summarize_nutrition(requirements, FACTS, 4)

    assert nutrition.total_kcal == Decimal("1310")
    assert nutrition.kcal_per_serving == Decimal("327.5")
    assert nutrition.has_estimates is False
    assert nutrition.uncounted_ingredients == ()


def test_pieces_and_volume_are_estimated_into_the_total() -> None:
    requirements = [
        make_requirement("mąka", "100", GRAM, FLOUR),
        make_requirement("jajka", "2", PIECE, EGGS),
        make_requirement("mleko", "500", MILLILITRE, MILK),
    ]

    nutrition = summarize_nutrition(requirements, FACTS, 2)

    assert nutrition.total_kcal == Decimal("865.2")
    assert nutrition.kcal_per_serving == Decimal("432.6")
    assert nutrition.has_estimates is True
    assert nutrition.uncounted_ingredients == ()


def test_lines_that_cannot_be_counted_are_listed_with_their_reason() -> None:
    requirements = [
        make_requirement("mąka", "100", GRAM, FLOUR),
        make_requirement("mąka w szklankach", "200", MILLILITRE, FLOUR),
        make_requirement("mleko", "2", PIECE, MILK),
        make_requirement("jajka", "1", PACKAGE, EGGS),
        make_requirement("szafran", "1", GRAM, None),
        RecipeRequirement(name="sól", ingredient_id=None, quantity=None),
    ]

    nutrition = summarize_nutrition(requirements, FACTS, 2)

    assert nutrition.total_kcal == Decimal("364")
    assert nutrition.kcal_per_serving == Decimal("182")
    assert nutrition.has_estimates is False
    assert nutrition.uncounted_ingredients == (
        UncountedIngredient(name="mąka w szklankach", reason=UncountedReason.NO_DENSITY),
        UncountedIngredient(name="mleko", reason=UncountedReason.NO_PIECE_WEIGHT),
        UncountedIngredient(name="jajka", reason=UncountedReason.NO_PACKAGE_WEIGHT),
        UncountedIngredient(name="szafran", reason=UncountedReason.NO_CALORIES),
        UncountedIngredient(name="sól", reason=UncountedReason.NO_AMOUNT),
    )


def test_a_tag_missing_from_the_facts_has_no_calories() -> None:
    requirements = [make_requirement("jajka", "120", GRAM, EGGS)]

    nutrition = summarize_nutrition(requirements, {}, 1)

    assert nutrition.uncounted_ingredients == (
        UncountedIngredient(name="jajka", reason=UncountedReason.NO_CALORIES),
    )


def test_unknown_servings_give_only_the_total() -> None:
    requirements = [make_requirement("mąka", "100", GRAM, FLOUR)]

    nutrition = summarize_nutrition(requirements, FACTS, None)

    assert nutrition.total_kcal == Decimal("364")
    assert nutrition.kcal_per_serving is None


def test_a_recipe_without_counted_lines_totals_zero() -> None:
    nutrition = summarize_nutrition([], FACTS, 2)

    assert nutrition.total_kcal == Decimal("0")
    assert nutrition.kcal_per_serving == Decimal("0")
    assert nutrition.has_estimates is False
