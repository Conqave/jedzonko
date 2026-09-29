from datetime import UTC, datetime
from decimal import Decimal

from recipes.application.use_cases.match_external_recipe_ingredients import (
    MatchExternalRecipeIngredients,
)
from recipes.domain.external import (
    ExternalRecipeDetail,
    ExternalRecipeIngredient,
    ExternalRecipePage,
    ExternalRecipeSummary,
)
from recipes.domain.external_line import IngredientChoice, LineInterpretation
from recipes.tests.factories import EGGS, MILK
from recipes.tests.fakes import (
    FakeIngredientLineInterpreter,
    FakeIngredientLineRepository,
    FakeRecipeSource,
    FakeTagVocabulary,
)

NOW = datetime(2026, 9, 29, 8, 0, tzinfo=UTC)
EMPTY_PAGE = ExternalRecipePage(recipes=(), page=0, page_size=12, total_count=0, total_pages=0)
EGGS_LINE = "3 średnie jajka"
MILK_LINE = "szklanka mleka"
EGGS_MEANING = LineInterpretation(ingredient_id=EGGS, quantity=Decimal("3"), unit_code="szt")
MILK_MEANING = LineInterpretation(ingredient_id=MILK, quantity=None, unit_code=None)


def _recipe(tags: tuple[str, ...]) -> ExternalRecipeDetail:
    summary = ExternalRecipeSummary(
        source_name="Ania Gotuje",
        source_url="https://aniagotuje.pl/przepis/omlet",
        reference="omlet",
        name="Omlet",
        description="",
        image_url=None,
        yield_label="",
        total_time_minutes=None,
        tag_names=tags,
    )
    ingredients = tuple(
        ExternalRecipeIngredient(line, line, None, None) for line in (EGGS_LINE, MILK_LINE)
    )
    return ExternalRecipeDetail(
        summary=summary,
        preparation_time_minutes=None,
        cooking_time_minutes=None,
        steps=(),
        ingredients=ingredients,
    )


def _matching(
    tags: tuple[IngredientChoice, ...], lines: FakeIngredientLineRepository
) -> tuple[MatchExternalRecipeIngredients, FakeIngredientLineInterpreter]:
    interpreter = FakeIngredientLineInterpreter({EGGS_LINE: EGGS_MEANING, MILK_LINE: MILK_MEANING})
    use_case = MatchExternalRecipeIngredients(
        FakeRecipeSource(EMPTY_PAGE, {"omlet": _recipe(("jajko",))}),
        FakeTagVocabulary(tags),
        lines,
        interpreter,
    )
    return use_case, interpreter


EGGS_TAG = IngredientChoice(id=EGGS, name="jajka")
MILK_TAG = IngredientChoice(id=MILK, name="mleko")


def test_lines_are_interpreted_against_the_whole_tag_catalog_and_stored() -> None:
    lines = FakeIngredientLineRepository({})
    use_case, interpreter = _matching((EGGS_TAG, MILK_TAG), lines)

    count = use_case.execute("omlet", NOW)

    assert count == 2
    assert interpreter.calls == [
        (
            (EGGS_LINE, MILK_LINE),
            (EGGS_TAG, MILK_TAG),
        )
    ]
    assert lines.interpretations["3 srednie jajka"] == EGGS_MEANING
    assert lines.saved_model_names == ["fake-model"]


def test_only_lines_never_seen_are_sent_to_the_model() -> None:
    lines = FakeIngredientLineRepository({"3 srednie jajka": EGGS_MEANING})
    use_case, interpreter = _matching((EGGS_TAG, MILK_TAG), lines)

    use_case.execute("omlet", NOW)

    assert [call[0] for call in interpreter.calls] == [(MILK_LINE,)]


def test_a_recipe_matched_before_needs_no_model() -> None:
    known = {"3 srednie jajka": EGGS_MEANING, "szklanka mleka": MILK_MEANING}
    use_case, interpreter = _matching((EGGS_TAG, MILK_TAG), FakeIngredientLineRepository(known))

    assert use_case.execute("omlet", NOW) == 0
    assert interpreter.calls == []


def test_an_empty_tag_catalog_has_nothing_to_choose_from() -> None:
    use_case, interpreter = _matching((), FakeIngredientLineRepository({}))

    assert use_case.execute("omlet", NOW) == 0
    assert interpreter.calls == []
