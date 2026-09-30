from decimal import Decimal
from io import StringIO
from pathlib import Path

import pytest
from django.contrib.auth.models import User
from django.core.management import CommandError, call_command
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient

from catalog.domain.ingredient import IngredientNameSource
from catalog.models import Ingredient
from config.composition import container
from tests.factories import make_ingredient

pytestmark = pytest.mark.django_db

SOURCE_URL = "https://example.org/nutrition/apple"


def _write_calories(path: Path, rows: list[str]) -> Path:
    lines = ["tag,kcal_per_100g,source_url", *rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _calories_of(ingredient: Ingredient) -> tuple[Decimal | None, str | None, str | None]:
    ingredient.refresh_from_db()
    return ingredient.kcal_per_100g, ingredient.kcal_source, ingredient.kcal_reference_url


@pytest.mark.parametrize(
    ("kcal", "source", "url"),
    [
        (Decimal("52"), None, None),
        (None, "manual", None),
        (Decimal("52"), "manual", SOURCE_URL),
        (Decimal("52"), "reference", None),
        (Decimal("52"), "reference", ""),
        (Decimal("52"), "model", None),
        (Decimal("950"), "manual", None),
        (Decimal("-1"), "manual", None),
    ],
)
def test_the_database_rejects_incoherent_calories(
    kcal: Decimal | None, source: str | None, url: str | None
) -> None:
    apple = make_ingredient("Jabłko")

    with pytest.raises(IntegrityError), transaction.atomic():
        Ingredient.objects.filter(pk=apple.pk).update(
            kcal_per_100g=kcal, kcal_source=source, kcal_reference_url=url
        )


def test_a_member_sets_and_clears_calories_of_a_tag(api_client: APIClient, ala: User) -> None:
    apple = make_ingredient("Jabłko")
    api_client.force_login(ala)

    saved = api_client.put(
        f"/api/ingredients/{apple.pk}/calories/", {"kcal_per_100g": "52.5"}, format="json"
    )
    found = api_client.get("/api/ingredients/?search=jabł")
    cleared = api_client.put(
        f"/api/ingredients/{apple.pk}/calories/", {"kcal_per_100g": None}, format="json"
    )

    assert saved.status_code == 200
    expected = {"kcal_per_100g": "52.5", "provenance": "manual", "reference_url": None}
    assert saved.data["calories"] == expected
    assert found.data[0]["calories"] == expected
    assert cleared.data["calories"] is None
    assert _calories_of(apple) == (None, None, None)


def test_invalid_calories_are_rejected(api_client: APIClient, ala: User) -> None:
    apple = make_ingredient("Jabłko")
    api_client.force_login(ala)

    too_high = api_client.put(
        f"/api/ingredients/{apple.pk}/calories/", {"kcal_per_100g": "901"}, format="json"
    )
    not_a_number = api_client.put(
        f"/api/ingredients/{apple.pk}/calories/", {"kcal_per_100g": "dużo"}, format="json"
    )

    assert too_high.status_code == 400
    assert too_high.data["code"] == "invalid_tag_calories"
    assert not_a_number.status_code == 400
    assert _calories_of(apple) == (None, None, None)


def test_calories_of_an_unknown_tag_cannot_be_set(api_client: APIClient, ala: User) -> None:
    api_client.force_login(ala)

    response = api_client.put(
        "/api/ingredients/404/calories/", {"kcal_per_100g": "52"}, format="json"
    )

    assert response.status_code == 404
    assert response.data["code"] == "ingredient_not_found"


def test_anonymous_caller_cannot_set_calories(api_client: APIClient) -> None:
    apple = make_ingredient("Jabłko")

    response = api_client.put(
        f"/api/ingredients/{apple.pk}/calories/", {"kcal_per_100g": "52"}, format="json"
    )

    assert response.status_code == 403


def test_the_command_imports_reference_calories_and_keeps_manual_ones(tmp_path: Path) -> None:
    apple = make_ingredient("Jabłko")
    flour = make_ingredient("Mąka pszenna")
    container().catalog.set_tag_calories.execute(flour.pk, Decimal("350"))
    path = _write_calories(
        tmp_path / "kcal.csv",
        [
            f"jabłko,52,{SOURCE_URL}",
            "mąka pszenna,364,https://example.org/flour",
            "kawior,264,https://example.org/c",
        ],
    )
    output = StringIO()

    call_command("import_tag_calories", str(path), stdout=output)

    assert "Updated 1, unchanged 0, skipped manual 1, unknown 1." in output.getvalue()
    assert _calories_of(apple) == (Decimal("52.0"), "reference", SOURCE_URL)
    assert _calories_of(flour) == (Decimal("350.0"), "manual", None)


def test_the_command_imports_nothing_from_a_file_naming_a_tag_twice(tmp_path: Path) -> None:
    apple = make_ingredient("Jabłko")
    eggs = make_ingredient("Jajka")
    container().catalog.add_ingredient_alias.execute(eggs.pk, "jajko", IngredientNameSource.MANUAL)
    path = _write_calories(
        tmp_path / "kcal.csv",
        [f"jabłko,52,{SOURCE_URL}", f"jajka,143,{SOURCE_URL}", f"jajko,150,{SOURCE_URL}"],
    )

    with pytest.raises(CommandError):
        call_command("import_tag_calories", str(path), stdout=StringIO())

    assert _calories_of(apple) == (None, None, None)
    assert _calories_of(eggs) == (None, None, None)


def test_the_command_refuses_a_malformed_file(tmp_path: Path) -> None:
    apple = make_ingredient("Jabłko")
    path = _write_calories(tmp_path / "kcal.csv", [f"jabłko,52,{SOURCE_URL}", "jajka,-3,x"])

    with pytest.raises(CommandError):
        call_command("import_tag_calories", str(path), stdout=StringIO())

    assert _calories_of(apple) == (None, None, None)
