from datetime import UTC, datetime

import pytest

from recipes.application.errors import (
    RecipeNotFoundAtSourceError,
    RecipeSourceContractError,
    RecipeSourceUnavailableError,
)
from recipes.application.use_cases.import_external_recipes import (
    ImportExternalRecipes,
    ImportOutcome,
)
from recipes.domain.external import ExternalRecipeIngredient, ImportedExternalRecipe, RecipeImage
from recipes.tests.fakes import FakeExternalRecipeCatalog, FakeRecipeSite, FakeTransactionManager

NOW = datetime(2026, 9, 30, 8, 0, tzinfo=UTC)
IMAGE = RecipeImage(filename="omlet.jpg", content=b"\xff\xd8jpeg")


def _recipe(reference: str, image_source_url: str | None = None) -> ImportedExternalRecipe:
    line = ExternalRecipeIngredient("2 jajka", "2 jajka", None, None)
    return ImportedExternalRecipe(
        reference=reference,
        name=reference.capitalize(),
        source_url=f"https://aniagotuje.pl/przepis/{reference}",
        image_source_url=image_source_url,
        yield_label=None,
        ingredients=(line,),
    )


def _run(
    site: FakeRecipeSite,
    catalog: FakeExternalRecipeCatalog,
    limit: int | None = None,
    refresh: bool = False,
) -> tuple[dict[str, ImportOutcome], list[str]]:
    reported: list[str] = []
    use_case = ImportExternalRecipes(site, catalog, FakeTransactionManager())
    run = use_case.execute(limit, refresh, NOW, lambda reference, _: reported.append(reference))
    return run.outcomes, reported


def test_new_recipes_are_stored_with_their_image() -> None:
    site = FakeRecipeSite(
        ("omlet",),
        {"omlet": _recipe("omlet", "https://cdn/omlet.jpg")},
        {"https://cdn/omlet.jpg": IMAGE},
    )
    catalog = FakeExternalRecipeCatalog()

    outcomes, reported = _run(site, catalog)

    assert outcomes == {"omlet": ImportOutcome.IMPORTED}
    assert reported == ["omlet"]
    assert catalog.images["omlet"] == IMAGE
    assert catalog.fetched_at["omlet"] == NOW


def test_stored_recipes_are_skipped_unless_refreshed() -> None:
    site = FakeRecipeSite(
        ("omlet", "zupa"), {"omlet": _recipe("omlet"), "zupa": _recipe("zupa")}, {}
    )
    catalog = FakeExternalRecipeCatalog()
    catalog.save_recipe(_recipe("omlet"), None, NOW)

    outcomes, _ = _run(site, catalog)
    assert site.fetched == ["zupa"]
    assert outcomes == {"zupa": ImportOutcome.IMPORTED}

    _run(site, catalog, refresh=True)
    assert site.fetched == ["zupa", "omlet", "zupa"]


def test_limit_bounds_the_number_of_fetched_recipes() -> None:
    references = ("a", "b", "c")
    site = FakeRecipeSite(references, {name: _recipe(name) for name in references}, {})

    outcomes, _ = _run(site, FakeExternalRecipeCatalog(), limit=2)

    assert list(outcomes) == ["a", "b"]


def test_missing_and_malformed_pages_are_reported_and_skipped() -> None:
    site = FakeRecipeSite(
        ("gone", "odd"),
        {"gone": RecipeNotFoundAtSourceError(), "odd": RecipeSourceContractError()},
        {},
    )
    catalog = FakeExternalRecipeCatalog()

    outcomes, _ = _run(site, catalog)

    assert outcomes == {"gone": ImportOutcome.MISSING, "odd": ImportOutcome.REJECTED}
    assert catalog.recipes == {}


def test_an_unavailable_site_stops_the_import() -> None:
    site = FakeRecipeSite(("omlet",), {"omlet": RecipeSourceUnavailableError()}, {})

    with pytest.raises(RecipeSourceUnavailableError):
        _run(site, FakeExternalRecipeCatalog())


def test_a_failed_image_keeps_the_recipe_and_is_retried_on_the_next_run() -> None:
    url = "https://cdn/omlet.jpg"
    site = FakeRecipeSite(
        ("omlet",), {"omlet": _recipe("omlet", url)}, {url: RecipeSourceUnavailableError()}
    )
    catalog = FakeExternalRecipeCatalog()

    outcomes, _ = _run(site, catalog)
    assert outcomes == {"omlet": ImportOutcome.IMPORTED_WITHOUT_IMAGE}
    assert "omlet" in catalog.recipes
    assert catalog.images == {}

    retry = FakeRecipeSite(("omlet",), {}, {url: IMAGE})
    outcomes, _ = _run(retry, catalog)
    assert outcomes == {"omlet": ImportOutcome.IMAGE_ADDED}
    assert retry.fetched == []
    assert catalog.images["omlet"] == IMAGE


def test_limit_must_be_positive() -> None:
    with pytest.raises(ValueError):
        _run(FakeRecipeSite((), {}, {}), FakeExternalRecipeCatalog(), limit=0)
