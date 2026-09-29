from datetime import UTC, datetime

from recipes.application.use_cases.match_external_recipe_ingredients import (
    MatchExternalRecipeIngredients,
)
from recipes.domain.external import (
    ExternalRecipeDetail,
    ExternalRecipeIngredient,
    ExternalRecipePage,
    ExternalRecipeSummary,
)
from recipes.tests.fakes import FakeIngredientLines, FakeRecipeSource

NOW = datetime(2026, 9, 29, 8, 0, tzinfo=UTC)
EMPTY_PAGE = ExternalRecipePage(recipes=(), page=0, page_size=12, total_count=0, total_pages=0)


def _recipe() -> ExternalRecipeDetail:
    summary = ExternalRecipeSummary(
        source_name="Ania Gotuje",
        source_url="https://aniagotuje.pl/przepis/omlet",
        reference="omlet",
        name="Omlet",
        description="",
        image_url=None,
        yield_label="",
        total_time_minutes=None,
        tag_names=("jajko",),
    )
    ingredients = tuple(
        ExternalRecipeIngredient(line, line, None, None)
        for line in ("3 średnie jajka", "szklanka mleka")
    )
    return ExternalRecipeDetail(
        summary=summary,
        preparation_time_minutes=None,
        cooking_time_minutes=None,
        steps=(),
        ingredients=ingredients,
    )


def test_every_line_of_the_recipe_is_sent_for_interpretation() -> None:
    lines = FakeIngredientLines({})
    use_case = MatchExternalRecipeIngredients(
        FakeRecipeSource(EMPTY_PAGE, {"omlet": _recipe()}), lines
    )

    count = use_case.execute("omlet", NOW)

    assert count == 2
    assert lines.interpreted == [("3 średnie jajka", "szklanka mleka")]
