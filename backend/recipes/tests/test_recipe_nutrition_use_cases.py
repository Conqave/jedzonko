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
)
from recipes.domain.external_line import LineInterpretation
from recipes.domain.models import RecipeDetail, RecipeSummary
from recipes.domain.nutrition import UncountedIngredient
from recipes.tests.factories import EGGS, FLOUR, GRAM, MILK, MILLILITRE, make_requirement
from recipes.tests.fakes import (
    FakeExternalRecipeCatalog,
    FakeIngredientCalories,
    FakeIngredientLines,
    FakeIngredientResolver,
    FakeRecipeRepository,
    FakeRecipeSource,
)
from shared.nutrition import UncountedReason

EMPTY_PAGE = ExternalRecipePage(recipes=(), page=0, page_size=12, total_count=0, total_pages=0)
KCAL = {FLOUR: Decimal("364"), EGGS: Decimal("143")}


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


def _pancakes() -> ExternalRecipeDetail:
    summary = ExternalRecipeSummary(
        source_name="Ania Gotuje",
        source_url="https://aniagotuje.pl/przepis/nalesniki",
        reference="nalesniki",
        name="Naleśniki",
        description="",
        image_url=None,
        yield_label="4 porcje",
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
            make_requirement("mleko", "500", MILLILITRE, MILK),
        ]
    }
    repository = FakeRecipeRepository([_recipe(4)], requirements)
    calories = FakeIngredientCalories(KCAL)

    nutrition = GetRecipeNutrition(repository, calories).execute(1)

    assert nutrition.total_kcal == Decimal("728")
    assert nutrition.kcal_per_serving == Decimal("182")
    assert nutrition.uncounted_ingredients == (
        UncountedIngredient(name="mleko", reason=UncountedReason.NOT_BY_MASS),
    )
    assert calories.asked == [{FLOUR, MILK}]


def test_nutrition_of_an_unknown_recipe_fails() -> None:
    repository = FakeRecipeRepository([], {})

    with pytest.raises(RecipeNotFoundError):
        GetRecipeNutrition(repository, FakeIngredientCalories(KCAL)).execute(1)


def test_external_recipe_nutrition_uses_interpreted_lines() -> None:
    interpretation = LineInterpretation(ingredient_id=EGGS, quantity=Decimal("120"), unit_code="g")
    lines = FakeIngredientLines({"2 jajka (ok. 120 g)": interpretation})
    use_case = GetExternalRecipeNutrition(
        FakeExternalRecipeCatalog(),
        FakeRecipeSource(EMPTY_PAGE, {"nalesniki": _pancakes()}),
        FakeIngredientResolver({"mąka": FLOUR, "mleko": MILK}),
        lines,
        FakeIngredientCalories(KCAL),
    )

    nutrition = use_case.execute("nalesniki")

    assert nutrition.total_kcal == Decimal("899.6")
    assert nutrition.kcal_per_serving is None
    assert nutrition.uncounted_ingredients == (
        UncountedIngredient(name="mleko", reason=UncountedReason.NOT_BY_MASS),
    )
