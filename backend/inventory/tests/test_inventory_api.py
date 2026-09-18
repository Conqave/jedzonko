from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from catalog.models import Ingredient, MeasurementUnit
from households.models import Household, HouseholdMembership
from inventory.models import InventoryItem

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def ala() -> User:
    return User.objects.create_user(username="ala", password="Ma-Kota-1234")


@pytest.fixture
def ola() -> User:
    return User.objects.create_user(username="ola", password="Ma-Psa-1234")


@pytest.fixture
def household(ala: User) -> Household:
    created = Household.objects.create(name="Dom Ali")
    HouseholdMembership.objects.create(household=created, user=ala)
    return created


@pytest.fixture
def flour() -> Ingredient:
    return Ingredient.objects.create(
        name="Mąka pszenna", default_unit=MeasurementUnit.objects.get(code="kg")
    )


def test_inventory_is_denied_for_anonymous_caller(api_client: APIClient) -> None:
    assert api_client.get("/api/inventory/", {"household_id": 1}).status_code == 403


def test_inventory_is_denied_for_non_member(
    api_client: APIClient, ola: User, household: Household
) -> None:
    api_client.force_login(ola)

    response = api_client.get("/api/inventory/", {"household_id": household.pk})

    assert response.status_code == 403
    assert response.data["code"] == "not_a_household_member"


def test_member_adds_and_lists_an_inventory_item(
    api_client: APIClient, ala: User, household: Household, flour: Ingredient
) -> None:
    api_client.force_login(ala)

    created = api_client.post(
        "/api/inventory/",
        {
            "household_id": household.pk,
            "ingredient_id": flour.pk,
            "quantity": "2.000",
            "unit_code": "kg",
            "minimum_quantity": "3.000",
        },
        format="json",
    )

    assert created.status_code == 201
    assert created.data["ingredient_name"] == "Mąka pszenna"
    assert created.data["below_minimum"] is True

    listed = api_client.get("/api/inventory/", {"household_id": household.pk})
    assert [item["id"] for item in listed.data] == [created.data["id"]]


def test_the_same_ingredient_cannot_be_added_twice(
    api_client: APIClient, ala: User, household: Household, flour: Ingredient
) -> None:
    api_client.force_login(ala)
    payload = {
        "household_id": household.pk,
        "ingredient_id": flour.pk,
        "quantity": "1.000",
        "unit_code": "kg",
    }
    api_client.post("/api/inventory/", payload, format="json")

    response = api_client.post("/api/inventory/", payload, format="json")

    assert response.status_code == 400
    assert response.data["code"] == "duplicate_inventory_item"


def test_unknown_unit_is_rejected(
    api_client: APIClient, ala: User, household: Household, flour: Ingredient
) -> None:
    api_client.force_login(ala)

    response = api_client.post(
        "/api/inventory/",
        {
            "household_id": household.pk,
            "ingredient_id": flour.pk,
            "quantity": "1.000",
            "unit_code": "parsek",
        },
        format="json",
    )

    assert response.status_code == 400
    assert response.data["code"] == "measurement_unit_not_found"


def test_corrected_quantity_becomes_authoritative(
    api_client: APIClient, ala: User, household: Household, flour: Ingredient
) -> None:
    item = InventoryItem.objects.create(
        household=household,
        ingredient=flour,
        unit=MeasurementUnit.objects.get(code="kg"),
        quantity=Decimal("2.000"),
    )
    api_client.force_login(ala)

    response = api_client.patch(f"/api/inventory/{item.pk}/", {"quantity": "0.500"}, format="json")

    assert response.status_code == 200
    assert response.data["quantity"] == "0.500"
    item.refresh_from_db()
    assert item.quantity == Decimal("0.500")


def test_non_member_cannot_touch_another_households_item(
    api_client: APIClient, ola: User, household: Household, flour: Ingredient
) -> None:
    item = InventoryItem.objects.create(
        household=household,
        ingredient=flour,
        unit=MeasurementUnit.objects.get(code="kg"),
        quantity=Decimal("2.000"),
    )
    api_client.force_login(ola)

    assert (
        api_client.patch(f"/api/inventory/{item.pk}/", {"quantity": "9"}, format="json").data[
            "code"
        ]
        == "not_a_household_member"
    )
    assert api_client.delete(f"/api/inventory/{item.pk}/").data["code"] == "not_a_household_member"


def test_missing_item_is_not_found(api_client: APIClient, ala: User) -> None:
    api_client.force_login(ala)

    response = api_client.delete("/api/inventory/999999/")

    assert response.status_code == 404
    assert response.data["code"] == "inventory_item_not_found"


def test_catalog_endpoints_expose_seeded_units(api_client: APIClient, ala: User) -> None:
    api_client.force_login(ala)

    units = api_client.get("/api/catalog/units/")

    assert units.status_code == 200
    assert {unit["code"] for unit in units.data} >= {"g", "kg", "ml", "l", "szt"}
