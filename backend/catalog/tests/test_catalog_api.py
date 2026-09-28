from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from catalog.models import Product
from households.models import Household
from tests.factories import confirm_ingredient, make_ingredient, make_product

pytestmark = pytest.mark.django_db


def test_products_are_denied_for_anonymous_caller(api_client: APIClient) -> None:
    response = api_client.get("/api/products/?household_id=1")

    assert response.status_code == 403


def test_member_creates_and_lists_a_product(
    api_client: APIClient, ala: User, household_a: Household
) -> None:
    api_client.force_login(ala)

    created = api_client.post(
        "/api/products/",
        {
            "household_id": household_a.pk,
            "name": "  Jaja   ściółkowe ",
            "default_unit_code": "opak",
            "package": {"quantity": "10", "unit_code": "szt"},
        },
        format="json",
    )
    listed = api_client.get(f"/api/products/?household_id={household_a.pk}")

    assert created.status_code == 201
    assert created.data["name"] == "Jaja ściółkowe"
    assert created.data["package"] == {"quantity": "10.000", "unit_code": "szt"}
    assert [entry["product"]["name"] for entry in listed.data] == ["Jaja ściółkowe"]
    assert listed.data[0]["ingredient_id"] is None


def test_search_ignores_polish_diacritics(
    api_client: APIClient, ala: User, household_a: Household
) -> None:
    make_product(household_a, "Mąka pszenna", "kg")
    make_product(household_a, "Cukier", "kg")
    api_client.force_login(ala)

    response = api_client.get(f"/api/products/?household_id={household_a.pk}&search=MAKA")

    assert [entry["product"]["name"] for entry in response.data] == ["Mąka pszenna"]


def test_the_same_normalized_name_cannot_be_created_twice(
    api_client: APIClient, ala: User, household_a: Household
) -> None:
    make_product(household_a, "Mąka pszenna", "kg")
    api_client.force_login(ala)

    response = api_client.post(
        "/api/products/",
        {"household_id": household_a.pk, "name": "maka PSZENNA", "default_unit_code": "kg"},
        format="json",
    )

    assert response.status_code == 400
    assert response.data["code"] == "duplicate_product"


def test_two_households_own_independent_products(
    api_client: APIClient, ala: User, household_a: Household, household_b: Household
) -> None:
    make_product(household_b, "Mąka pszenna", "kg")
    api_client.force_login(ala)

    created = api_client.post(
        "/api/products/",
        {"household_id": household_a.pk, "name": "Mąka pszenna", "default_unit_code": "kg"},
        format="json",
    )

    assert created.status_code == 201
    assert Product.objects.filter(normalized_name="maka pszenna").count() == 2


@pytest.mark.parametrize(
    ("payload", "code"),
    [
        ({"name": "Mleko", "default_unit_code": "beczka"}, "measurement_unit_not_found"),
        (
            {
                "name": "Mleko",
                "default_unit_code": "l",
                "package": {"quantity": "1", "unit_code": "beczka"},
            },
            "measurement_unit_not_found",
        ),
        ({"name": "   ", "default_unit_code": "l"}, "blank"),
    ],
)
def test_invalid_products_are_rejected(
    api_client: APIClient,
    ala: User,
    household_a: Household,
    payload: dict[str, object],
    code: str,
) -> None:
    api_client.force_login(ala)

    response = api_client.post(
        "/api/products/", {"household_id": household_a.pk, **payload}, format="json"
    )

    assert response.status_code == 400
    assert code in str(response.data)


def test_non_member_can_neither_read_nor_create(
    api_client: APIClient, ola: User, household_a: Household
) -> None:
    api_client.force_login(ola)

    listed = api_client.get(f"/api/products/?household_id={household_a.pk}")
    created = api_client.post(
        "/api/products/",
        {"household_id": household_a.pk, "name": "Mleko", "default_unit_code": "l"},
        format="json",
    )

    assert listed.status_code == 403
    assert created.status_code == 403
    assert created.data["code"] == "not_a_household_member"


def test_member_renames_a_product_and_sets_its_package(
    api_client: APIClient, ala: User, household_a: Household
) -> None:
    product = make_product(household_a, "Jaja", "opak")
    api_client.force_login(ala)

    response = api_client.patch(
        f"/api/products/{product.pk}/",
        {"name": "Jaja ściółkowe", "package": {"quantity": "10", "unit_code": "szt"}},
        format="json",
    )

    assert response.status_code == 200
    product.refresh_from_db()
    assert (product.name, product.package_quantity, product.package_unit_code) == (
        "Jaja ściółkowe",
        Decimal("10.000"),
        "szt",
    )


def test_member_confirms_and_rejects_a_products_ingredient(
    api_client: APIClient, ala: User, household_a: Household
) -> None:
    product = make_product(household_a, "Jaja ściółkowe", "opak")
    eggs = make_ingredient("Jajka")
    butter = make_ingredient("Masło")
    api_client.force_login(ala)

    wrong = api_client.post(f"/api/products/{product.pk}/ingredients/{butter.pk}/confirmation/")
    right = api_client.post(f"/api/products/{product.pk}/ingredients/{eggs.pk}/confirmation/")
    links = api_client.get(f"/api/products/{product.pk}/ingredients/")
    listed = api_client.get(f"/api/products/?household_id={household_a.pk}")

    assert (wrong.status_code, right.status_code) == (204, 204)
    decisions = {entry["ingredient"]["name"]: entry["status"] for entry in links.data}
    assert decisions == {"Masło": "rejected", "Jajka": "confirmed"}
    assert listed.data[0]["ingredient_name"] == "Jajka"


def test_rejecting_twice_is_reported(
    api_client: APIClient, ala: User, household_a: Household
) -> None:
    product = make_product(household_a, "Jaja", "opak")
    eggs = make_ingredient("Jajka")
    confirm_ingredient(ala, product, eggs)
    api_client.force_login(ala)

    first = api_client.post(f"/api/products/{product.pk}/ingredients/{eggs.pk}/rejection/")
    second = api_client.post(f"/api/products/{product.pk}/ingredients/{eggs.pk}/rejection/")

    assert first.status_code == 204
    assert second.status_code == 400
    assert second.data["code"] == "invalid_product_ingredient_transition"


def test_a_foreign_product_cannot_be_classified(
    api_client: APIClient, ola: User, household_a: Household
) -> None:
    product = make_product(household_a, "Jaja", "opak")
    eggs = make_ingredient("Jajka")
    api_client.force_login(ola)

    response = api_client.post(f"/api/products/{product.pk}/ingredients/{eggs.pk}/confirmation/")

    assert response.status_code == 403


def test_ingredients_are_searched_by_any_of_their_names(api_client: APIClient, ala: User) -> None:
    make_ingredient("Jajka")
    make_ingredient("Masło")
    api_client.force_login(ala)

    response = api_client.get("/api/ingredients/?search=JAJ")

    assert [entry["name"] for entry in response.data] == ["Jajka"]


def test_units_come_from_code_constants(api_client: APIClient, ala: User) -> None:
    api_client.force_login(ala)

    response = api_client.get("/api/units/")

    by_code = {unit["code"]: unit for unit in response.data}
    assert set(by_code) == {"g", "kg", "ml", "l", "szt", "opak"}
    assert by_code["kg"] == {"code": "kg", "name": "kilogram", "dimension": "mass"}
