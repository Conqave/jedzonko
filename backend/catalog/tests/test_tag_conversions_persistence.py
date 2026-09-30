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

SOURCE_URL = "https://example.org/nutrition/egg"
Fact = tuple[Decimal | None, str | None, str | None]


def _write_conversions(path: Path, rows: list[str]) -> Path:
    lines = ["tag,grams_per_piece,grams_per_ml,source_url", *rows]
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")
    return path


def _piece_weight_of(ingredient: Ingredient) -> Fact:
    ingredient.refresh_from_db()
    return (
        ingredient.grams_per_piece,
        ingredient.piece_weight_source,
        ingredient.piece_weight_reference_url,
    )


def _density_of(ingredient: Ingredient) -> Fact:
    ingredient.refresh_from_db()
    return ingredient.grams_per_ml, ingredient.density_source, ingredient.density_reference_url


INCOHERENT_PROVENANCE = [
    (Decimal("1"), None, None),
    (None, "manual", None),
    (None, None, SOURCE_URL),
    (None, "reference", SOURCE_URL),
    (Decimal("1"), "manual", SOURCE_URL),
    (Decimal("1"), "reference", None),
    (Decimal("1"), "reference", ""),
    (Decimal("1"), "model", None),
    (Decimal("0"), "manual", None),
    (Decimal("-1"), "manual", None),
]


@pytest.mark.parametrize(
    ("grams", "source", "url"), [*INCOHERENT_PROVENANCE, (Decimal("10001"), "manual", None)]
)
def test_the_database_rejects_an_incoherent_piece_weight(
    grams: Decimal | None, source: str | None, url: str | None
) -> None:
    egg = make_ingredient("Jajka")

    with pytest.raises(IntegrityError), transaction.atomic():
        Ingredient.objects.filter(pk=egg.pk).update(
            grams_per_piece=grams, piece_weight_source=source, piece_weight_reference_url=url
        )


@pytest.mark.parametrize(
    ("grams_per_ml", "source", "url"), [*INCOHERENT_PROVENANCE, (Decimal("3.5"), "manual", None)]
)
def test_the_database_rejects_an_incoherent_density(
    grams_per_ml: Decimal | None, source: str | None, url: str | None
) -> None:
    milk = make_ingredient("Mleko")

    with pytest.raises(IntegrityError), transaction.atomic():
        Ingredient.objects.filter(pk=milk.pk).update(
            grams_per_ml=grams_per_ml, density_source=source, density_reference_url=url
        )


def test_the_database_keeps_coherent_conversions() -> None:
    egg = make_ingredient("Jajka")

    Ingredient.objects.filter(pk=egg.pk).update(
        grams_per_piece=Decimal("10000"),
        piece_weight_source="reference",
        piece_weight_reference_url=SOURCE_URL,
        grams_per_ml=Decimal("3"),
        density_source="manual",
    )

    assert _piece_weight_of(egg) == (Decimal("10000.0"), "reference", SOURCE_URL)
    assert _density_of(egg) == (Decimal("3.000"), "manual", None)


def test_a_member_sets_and_clears_the_conversions_of_a_tag(
    api_client: APIClient, ala: User
) -> None:
    egg = make_ingredient("Jajka")
    api_client.force_login(ala)

    piece = api_client.put(
        f"/api/ingredients/{egg.pk}/piece-weight/", {"grams_per_piece": "55.5"}, format="json"
    )
    density = api_client.put(
        f"/api/ingredients/{egg.pk}/density/", {"grams_per_ml": "1.031"}, format="json"
    )
    found = api_client.get("/api/ingredients/?search=jaj")
    cleared = api_client.put(
        f"/api/ingredients/{egg.pk}/piece-weight/", {"grams_per_piece": None}, format="json"
    )

    expected_piece = {"grams_per_piece": "55.5", "provenance": "manual", "reference_url": None}
    expected_density = {"grams_per_ml": "1.031", "provenance": "manual", "reference_url": None}
    assert piece.status_code == 200
    assert piece.data["piece_weight"] == expected_piece
    assert density.data["density"] == expected_density
    assert found.data[0]["piece_weight"] == expected_piece
    assert found.data[0]["density"] == expected_density
    assert cleared.data["piece_weight"] is None
    assert cleared.data["density"] == expected_density
    assert _piece_weight_of(egg) == (None, None, None)
    assert _density_of(egg) == (Decimal("1.031"), "manual", None)


def test_invalid_conversions_are_rejected(api_client: APIClient, ala: User) -> None:
    egg = make_ingredient("Jajka")
    api_client.force_login(ala)

    no_weight = api_client.put(
        f"/api/ingredients/{egg.pk}/piece-weight/", {"grams_per_piece": "0"}, format="json"
    )
    too_heavy = api_client.put(
        f"/api/ingredients/{egg.pk}/piece-weight/", {"grams_per_piece": "20000"}, format="json"
    )
    too_dense = api_client.put(
        f"/api/ingredients/{egg.pk}/density/", {"grams_per_ml": "3.5"}, format="json"
    )
    not_a_number = api_client.put(
        f"/api/ingredients/{egg.pk}/density/", {"grams_per_ml": "gęsto"}, format="json"
    )

    assert no_weight.status_code == 400
    assert no_weight.data["code"] == "invalid_piece_weight"
    assert too_heavy.data["code"] == "invalid_piece_weight"
    assert too_dense.status_code == 400
    assert too_dense.data["code"] == "invalid_density"
    assert not_a_number.status_code == 400
    assert _piece_weight_of(egg) == (None, None, None)
    assert _density_of(egg) == (None, None, None)


def test_conversions_of_an_unknown_tag_cannot_be_set(api_client: APIClient, ala: User) -> None:
    api_client.force_login(ala)

    piece = api_client.put(
        "/api/ingredients/404/piece-weight/", {"grams_per_piece": "55"}, format="json"
    )
    density = api_client.put("/api/ingredients/404/density/", {"grams_per_ml": "1"}, format="json")

    assert piece.status_code == 404
    assert piece.data["code"] == "ingredient_not_found"
    assert density.status_code == 404


def test_anonymous_caller_cannot_set_conversions(api_client: APIClient) -> None:
    egg = make_ingredient("Jajka")

    piece = api_client.put(
        f"/api/ingredients/{egg.pk}/piece-weight/", {"grams_per_piece": "55"}, format="json"
    )
    density = api_client.put(
        f"/api/ingredients/{egg.pk}/density/", {"grams_per_ml": "1"}, format="json"
    )

    assert piece.status_code == 403
    assert density.status_code == 403


def test_the_command_imports_reference_conversions_and_keeps_manual_ones(tmp_path: Path) -> None:
    egg = make_ingredient("Jajka")
    milk = make_ingredient("Mleko")
    container().catalog.set_tag_piece_weight.execute(egg.pk, Decimal("60"))
    path = _write_conversions(
        tmp_path / "conversions.csv",
        [
            f"jajka,55,,{SOURCE_URL}",
            f"mleko,,1.03,{SOURCE_URL}",
            f"kawior,0.1,,{SOURCE_URL}",
        ],
    )
    output = StringIO()

    call_command("import_tag_conversions", str(path), stdout=output)

    report = output.getvalue()
    assert "Updated 1, unchanged 0, skipped manual 1, unknown 1." in report
    assert "+ Mleko (grams_per_ml)" in report
    assert "= Jajka (grams_per_piece, manual value kept)" in report
    assert _piece_weight_of(egg) == (Decimal("60.0"), "manual", None)
    assert _density_of(egg) == (None, None, None)
    assert _density_of(milk) == (Decimal("1.030"), "reference", SOURCE_URL)


def test_the_conversion_command_imports_nothing_from_a_file_naming_a_tag_twice(
    tmp_path: Path,
) -> None:
    eggs = make_ingredient("Jajka")
    container().catalog.add_ingredient_alias.execute(eggs.pk, "jajko", IngredientNameSource.MANUAL)
    path = _write_conversions(
        tmp_path / "conversions.csv", [f"jajka,55,,{SOURCE_URL}", f"jajko,,1.03,{SOURCE_URL}"]
    )

    with pytest.raises(CommandError):
        call_command("import_tag_conversions", str(path), stdout=StringIO())

    assert _piece_weight_of(eggs) == (None, None, None)


def test_the_conversion_command_refuses_a_malformed_file(tmp_path: Path) -> None:
    eggs = make_ingredient("Jajka")
    path = _write_conversions(
        tmp_path / "conversions.csv", [f"jajka,55,,{SOURCE_URL}", "mleko,,,x"]
    )

    with pytest.raises(CommandError):
        call_command("import_tag_conversions", str(path), stdout=StringIO())

    assert _piece_weight_of(eggs) == (None, None, None)
