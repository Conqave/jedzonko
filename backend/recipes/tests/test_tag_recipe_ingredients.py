from datetime import UTC, datetime
from decimal import Decimal

from recipes.application.use_cases.tag_recipe_ingredients import TagRecipeIngredients
from recipes.domain.difficulty import RecipeDifficulty
from recipes.domain.external_line import LineInterpretation
from recipes.domain.models import RecipeDetail, RecipeIngredientDetail, RecipeSummary
from recipes.tests.fakes import FakeIngredientLines, FakeRecipeRepository

NOW = datetime(2026, 9, 29, 23, 0, tzinfo=UTC)


def _recipe() -> RecipeDetail:
    summary = RecipeSummary(
        id=1,
        name="Kasza",
        description="",
        servings=2,
        preparation_time_minutes=0,
        cooking_time_minutes=0,
        difficulty=RecipeDifficulty.EASY,
        category=None,
        tag_names=(),
        image_url=None,
        author_username="ala",
    )
    ingredients = (
        RecipeIngredientDetail("kasza gryczana", None, Decimal("200"), "g"),
        RecipeIngredientDetail("sól", 7, Decimal("1"), "g"),
        RecipeIngredientDetail("coś", None, Decimal("1"), "g"),
    )
    return RecipeDetail(summary=summary, steps=(), ingredients=ingredients)


def test_untagged_recipe_lines_get_the_tag_the_model_found() -> None:
    repository = FakeRecipeRepository([_recipe()], {})
    lines = FakeIngredientLines(
        {"kasza gryczana": LineInterpretation(ingredient_id=40, quantity=None, unit_code=None)}
    )

    run = TagRecipeIngredients(repository, lines).execute(NOW)

    assert lines.interpreted == [("coś", "kasza gryczana")]
    assert repository.tagged == [("kasza gryczana", 40)]
    assert (run.tagged, run.untagged) == (("kasza gryczana",), ("coś",))
