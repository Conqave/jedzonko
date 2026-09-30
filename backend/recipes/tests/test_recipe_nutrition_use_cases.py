from datetime import UTC, datetime
from decimal import Decimal

import pytest

from recipes.application.errors import RecipeNotFoundError
from recipes.application.use_cases.get_external_recipe_nutrition import (
    GetExternalRecipeNutrition,
)
from recipes.application.use_cases.get_recipe_nutrition import GetRecipeNutrition
from recipes.domain.difficulty import RecipeDifficulty
from recipes.domain.external import (
    ExternalRecipeDetail,
    ExternalRecipeIngredient,
    ExternalRecipePage,
    ExternalRecipeSummary,
    ImportedExternalRecipe,
)
from recipes.domain.external_line import LineInterpretation
from recipes.domain.models import RecipeDetail, RecipeSummary
from recipes.domain.nutrition import RecipeNutrition, UncountedIngredient
from recipes.tests.factories import EGGS, FLOUR, GRAM, MILK, MILLILITRE, PIECE, make_requirement
from recipes.tests.fakes import (
    FakeExternalRecipeCatalog,
    FakeIngredientLines,
    FakeIngredientNutritionFacts,
    FakeIngredientResolver,
    FakeRecipeRepository,
    FakeRecipeSource,
)
from shared.nutrition import NutritionFacts, UncountedReason

NOW = datetime(2026, 9, 30, 12, 0, tzinfo=UTC)
EMPTY_PAGE = ExternalRecipePage(recipes=(), page=0, page_size=12, total_count=0, total_pages=0)
FACTS = {
    FLOUR: NutritionFacts(kcal_per_100g=Decimal("364"), grams_per_piece=None, grams_per_ml=None),
    EGGS: NutritionFacts(
        kcal_per_100g=Decimal("143"), grams_per_piece=Decimal("55"), grams_per_ml=None
    ),
    MILK: NutritionFacts(kcal_per_100g=Decimal("64"), grams_per_piece=None, grams_per_ml=None),
}


def _recipe(servings: int) -> RecipeDetail:
    summary = RecipeSummary(
        id=1,
        name="naleśniki",
        description="",
        servings=servings,
        preparation_time_minutes=5,
        cooking_time_minutes=15,
        difficulty=RecipeDifficulty.EASY,
        category=None,
        tag_names=(),
        image_url=None,
        author_username="ala",
    )
    return RecipeDetail(summary=summary, steps=(), ingredients=())


def _pancakes(yield_label: str = "4 porcje") -> ExternalRecipeDetail:
    summary = ExternalRecipeSummary(
        source_name="Ania Gotuje",
        source_url="https://aniagotuje.pl/przepis/nalesniki",
        reference="nalesniki",
        name="Naleśniki",
        description="",
        image_url=None,
        yield_label=yield_label,
        total_time_minutes=30,
        tag_names=(),
    )
    ingredients = (
        ExternalRecipeIngredient("200 g mąki", "mąka", Decimal("200"), "g"),
        ExternalRecipeIngredient("2 jajka (ok. 120 g)", "jajka", None, None),
        ExternalRecipeIngredient("500 ml mleka", "mleko", Decimal("500"), "ml"),
    )
    return ExternalRecipeDetail(
        summary=summary,
        preparation_time_minutes=10,
        cooking_time_minutes=20,
        steps=("Usmaż.",),
        ingredients=ingredients,
    )


def test_custom_recipe_nutrition_counts_per_serving() -> None:
    requirements = {
        1: [
            make_requirement("mąka", "200", GRAM, FLOUR),
            make_requirement("jajka", "2", PIECE, EGGS),
            make_requirement("mleko", "500", MILLILITRE, MILK),
        ]
    }
    repository = FakeRecipeRepository([_recipe(4)], requirements)
    facts = FakeIngredientNutritionFacts(FACTS)

    nutrition = GetRecipeNutrition(repository, facts).execute(1)

    assert nutrition.total_kcal == Decimal("885.3")
    assert nutrition.kcal_per_serving == Decimal("221.325")
    assert nutrition.has_estimates is True
    assert nutrition.uncounted_ingredients == (
        UncountedIngredient(name="mleko", reason=UncountedReason.NO_DENSITY),
    )
    assert facts.asked == [{FLOUR, EGGS, MILK}]


def test_nutrition_of_an_unknown_recipe_fails() -> None:
    repository = FakeRecipeRepository([], {})

    with pytest.raises(RecipeNotFoundError):
        GetRecipeNutrition(repository, FakeIngredientNutritionFacts(FACTS)).execute(1)


def _external_nutrition(catalog: FakeExternalRecipeCatalog, yield_label: str) -> RecipeNutrition:
    interpretation = LineInterpretation(ingredient_id=EGGS, quantity=Decimal("120"), unit_code="g")
    lines = FakeIngredientLines({"2 jajka (ok. 120 g)": interpretation})
    use_case = GetExternalRecipeNutrition(
        catalog,
        FakeRecipeSource(EMPTY_PAGE, {"nalesniki": _pancakes(yield_label)}),
        FakeIngredientResolver({"mąka": FLOUR, "mleko": MILK, "jajka": EGGS}),
        lines,
        FakeIngredientNutritionFacts(FACTS),
    )
    return use_case.execute("nalesniki")


def test_external_recipe_nutrition_uses_interpreted_lines_and_the_fetched_yield() -> None:
    nutrition = _external_nutrition(FakeExternalRecipeCatalog(), "4 porcje")

    assert nutrition.total_kcal == Decimal("899.6")
    assert nutrition.kcal_per_serving == Decimal("224.9")
    assert nutrition.has_estimates is False
    assert nutrition.uncounted_ingredients == (
        UncountedIngredient(name="mleko", reason=UncountedReason.NO_DENSITY),
    )


def test_external_recipe_without_a_stated_count_has_no_per_serving_value() -> None:
    nutrition = _external_nutrition(FakeExternalRecipeCatalog(), "forma 24 x 24 cm")

    assert nutrition.total_kcal == Decimal("899.6")
    assert nutrition.kcal_per_serving is None


def test_external_recipe_nutrition_prefers_the_stored_recipe_and_its_yield() -> None:
    catalog = FakeExternalRecipeCatalog()
    stored = ImportedExternalRecipe(
        reference="nalesniki",
        name="Naleśniki",
        source_url="https://aniagotuje.pl/przepis/nalesniki",
        image_source_url=None,
        yield_label="dla 2 osób",
        ingredients=(ExternalRecipeIngredient("3 jajka", "jajka", Decimal("3"), "szt"),),
    )
    catalog.save_recipe(stored, None, NOW)

    nutrition = _external_nutrition(catalog, "4 porcje")

    assert nutrition.total_kcal == Decimal("235.95")
    assert nutrition.kcal_per_serving == Decimal("117.975")
    assert nutrition.has_estimates is True
