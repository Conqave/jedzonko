from datetime import UTC, datetime
from decimal import Decimal

import pytest

from recipes.application.use_cases.tag_external_recipe_lines import TagExternalRecipeLines
from recipes.domain.external import ExternalRecipeIngredient, ImportedExternalRecipe
from recipes.domain.external_line import LineInterpretation
from recipes.tests.fakes import FakeExternalRecipeCatalog, FakeIngredientLines

NOW = datetime(2026, 9, 30, 8, 0, tzinfo=UTC)
TEXTS = ("2 jajka", "mleko", "sól", "masło")


def _catalog() -> FakeExternalRecipeCatalog:
    catalog = FakeExternalRecipeCatalog()
    lines = tuple(ExternalRecipeIngredient(text, text, None, None) for text in TEXTS)
    recipe = ImportedExternalRecipe(
        reference="omlet",
        name="Omlet",
        source_url="https://aniagotuje.pl/przepis/omlet",
        image_source_url=None,
        yield_label=None,
        ingredients=lines,
    )
    catalog.save_recipe(recipe, None, NOW)
    return catalog


def test_only_uninterpreted_lines_are_sent_in_batches() -> None:
    known = LineInterpretation(ingredient_id=1, quantity=Decimal("1"), unit_code="g")
    lines = FakeIngredientLines({"mleko": known})
    progress: list[tuple[int, int]] = []

    run = TagExternalRecipeLines(_catalog(), lines).execute(
        2, None, NOW, lambda done, total: progress.append((done, total))
    )

    assert lines.interpreted == [("2 jajka", "masło"), ("sól",)]
    assert progress == [(2, 3), (3, 3)]
    assert (run.pending_count, run.selected_count, run.interpreted_count) == (3, 3, 3)
    assert run.skipped_count == 0


def test_limit_bounds_the_lines_sent() -> None:
    lines = FakeIngredientLines({})

    run = TagExternalRecipeLines(_catalog(), lines).execute(10, 1, NOW, lambda done, total: None)

    assert lines.interpreted == [("2 jajka",)]
    assert run.pending_count == 4


def test_batch_size_must_be_positive() -> None:
    with pytest.raises(ValueError):
        TagExternalRecipeLines(_catalog(), FakeIngredientLines({})).execute(
            0, None, NOW, lambda done, total: None
        )


def test_a_garbled_batch_is_skipped_and_the_run_goes_on() -> None:
    lines = FakeIngredientLines({}, garbled=frozenset({"mleko"}))

    run = TagExternalRecipeLines(_catalog(), lines).execute(2, None, NOW, lambda done, total: None)

    assert lines.interpreted == [("2 jajka", "masło"), ("mleko", "sól")]
    assert (run.interpreted_count, run.skipped_count) == (2, 2)
