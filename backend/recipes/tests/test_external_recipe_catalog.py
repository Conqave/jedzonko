from collections.abc import Iterator
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest
from django.test import override_settings

from recipes.domain.external import ExternalRecipeIngredient, ImportedExternalRecipe, RecipeImage
from recipes.infrastructure.django_external_recipe_catalog import DjangoExternalRecipeCatalog
from recipes.models import ExternalRecipe

pytestmark = pytest.mark.django_db

NOW = datetime(2026, 9, 30, 8, 0, tzinfo=UTC)
IMAGE_URL = "https://cdn.aniagotuje.com/omlet.jpg"
IMAGE = RecipeImage(filename="omlet.jpg", content=b"\xff\xd8jpeg")


@pytest.fixture(autouse=True)
def media_root(tmp_path: Path) -> Iterator[Path]:
    with override_settings(MEDIA_ROOT=tmp_path):
        yield tmp_path


def _recipe(
    texts: tuple[str, ...], image_source_url: str | None = IMAGE_URL
) -> ImportedExternalRecipe:
    lines = tuple(
        ExternalRecipeIngredient(text, text.split(" - ")[0], None, None) for text in texts
    )
    weighed = ExternalRecipeIngredient("mąka - 200 g", "mąka", Decimal("200"), "g")
    return ImportedExternalRecipe(
        reference="omlet",
        name="Omlet",
        source_url="https://aniagotuje.pl/przepis/omlet",
        image_source_url=image_source_url,
        yield_label="2 porcje",
        ingredients=(*lines, weighed),
    )


def test_saved_recipe_keeps_its_lines_in_order_and_its_image_as_a_file(media_root: Path) -> None:
    catalog = DjangoExternalRecipeCatalog("Ania Gotuje")

    catalog.save_recipe(_recipe(("2 jajka", "mleko")), IMAGE, NOW)

    ingredients = catalog.find_ingredients("omlet")
    assert ingredients is not None
    assert [line.source_text for line in ingredients] == ["2 jajka", "mleko", "mąka - 200 g"]
    assert ingredients[2].quantity == Decimal("200")
    assert catalog.list_references() == frozenset({"omlet"})
    assert catalog.list_missing_images() == {}
    urls = catalog.find_image_urls(("omlet", "zupa"))
    assert list(urls) == ["omlet"]
    row = ExternalRecipe.objects.get()
    stored_name = str(row.image.name)
    assert stored_name.startswith("external_recipes/omlet")
    assert (media_root / stored_name).read_bytes() == IMAGE.content


def test_refresh_replaces_lines_and_keeps_an_image_that_failed_to_download_again() -> None:
    catalog = DjangoExternalRecipeCatalog("Ania Gotuje")
    catalog.save_recipe(_recipe(("2 jajka",)), IMAGE, NOW)

    catalog.save_recipe(_recipe(("3 jajka",)), None, NOW)

    ingredients = catalog.find_ingredients("omlet")
    assert ingredients is not None
    assert [line.source_text for line in ingredients] == ["3 jajka", "mąka - 200 g"]
    assert list(catalog.find_image_urls(("omlet",))) == ["omlet"]


def test_recipe_without_downloaded_image_is_listed_for_a_retry() -> None:
    catalog = DjangoExternalRecipeCatalog("Ania Gotuje")
    catalog.save_recipe(_recipe(("2 jajka",)), None, NOW)

    assert catalog.list_missing_images() == {"omlet": IMAGE_URL}

    catalog.save_image("omlet", IMAGE)

    assert catalog.list_missing_images() == {}


def test_distinct_line_texts_are_listed_for_interpretation() -> None:
    catalog = DjangoExternalRecipeCatalog("Ania Gotuje")
    catalog.save_recipe(_recipe(("mleko", "2 jajka")), None, NOW)

    texts = catalog.list_ingredient_texts()
    assert sorted(texts) == sorted(("2 jajka", "mleko", "mąka - 200 g"))


def test_unknown_recipe_has_no_stored_ingredients() -> None:
    assert DjangoExternalRecipeCatalog("Ania Gotuje").find_ingredients("zupa") is None
