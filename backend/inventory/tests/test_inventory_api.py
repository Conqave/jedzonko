from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from catalog.models import Product
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
def flour(household: Household) -> Product:
    return Product.objects.create(
        household=household,
        name="Mąka pszenna",
        normalized_name="maka pszenna",
        default_unit_code="kg",
        is_food=True,
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
    api_client: APIClient, ala: User, household: Household, flour: Product
) -> None:
    api_client.force_login(ala)

    created = api_client.post(
        "/api/inventory/",
        {
            "household_id": household.pk,
            "product_id": flour.pk,
            "quantity": "2.000",
            "unit_code": "kg",
            "minimum_quantity": "3.000",
        },
        format="json",
    )

    assert created.status_code == 201
    assert created.data["product_name"] == "Mąka pszenna"
    assert created.data["below_minimum"] is True

    listed = api_client.get("/api/inventory/", {"household_id": household.pk})
    assert [item["id"] for item in listed.data] == [created.data["id"]]


def test_the_same_product_cannot_be_added_twice(
    api_client: APIClient, ala: User, household: Household, flour: Product
) -> None:
    api_client.force_login(ala)
    payload = {
        "household_id": household.pk,
        "product_id": flour.pk,
        "quantity": "1.000",
        "unit_code": "kg",
    }
    api_client.post("/api/inventory/", payload, format="json")

    response = api_client.post("/api/inventory/", payload, format="json")

    assert response.status_code == 400
    assert response.data["code"] == "duplicate_inventory_item"


def test_unknown_unit_is_rejected(
    api_client: APIClient, ala: User, household: Household, flour: Product
) -> None:
    api_client.force_login(ala)

    response = api_client.post(
        "/api/inventory/",
        {
            "household_id": household.pk,
            "product_id": flour.pk,
            "quantity": "1.000",
            "unit_code": "parsek",
        },
        format="json",
    )

    assert response.status_code == 400
    assert response.data["code"] == "measurement_unit_not_found"


def test_unknown_product_is_rejected(
    api_client: APIClient, ala: User, household: Household
) -> None:
    api_client.force_login(ala)

    response = api_client.post(
        "/api/inventory/",
        {
            "household_id": household.pk,
            "product_id": 999999,
            "quantity": "1.000",
            "unit_code": "kg",
        },
        format="json",
    )

    assert response.status_code == 400
    assert response.data["code"] == "product_not_found"


def test_corrected_quantity_becomes_authoritative(
    api_client: APIClient, ala: User, household: Household, flour: Product
) -> None:
    item = InventoryItem.objects.create(product=flour, unit_code="kg", quantity=Decimal("2.000"))
    api_client.force_login(ala)

    response = api_client.patch(f"/api/inventory/{item.pk}/", {"quantity": "0.500"}, format="json")

    assert response.status_code == 200
    assert response.data["quantity"] == "0.500"
    item.refresh_from_db()
    assert item.quantity == Decimal("0.500")


def test_non_member_cannot_touch_another_households_item(
    api_client: APIClient, ola: User, household: Household, flour: Product
) -> None:
    item = InventoryItem.objects.create(product=flour, unit_code="kg", quantity=Decimal("2.000"))
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


def test_item_edit_changes_name_quantity_and_unit_in_place(
    api_client: APIClient, ala: User, household: Household, flour: Product
) -> None:
    item = InventoryItem.objects.create(product=flour, unit_code="kg", quantity=Decimal("2.000"))
    api_client.force_login(ala)

    response = api_client.patch(
        f"/api/inventory/{item.pk}/",
        {"product_name": "Mąka żytnia", "quantity": "1.500", "unit_code": "g"},
        format="json",
    )

    assert response.status_code == 200
    assert response.data["id"] == item.pk
    assert response.data["product_id"] == flour.pk
    assert response.data["product_name"] == "Mąka żytnia"
    assert response.data["unit_code"] == "g"
    item.refresh_from_db()
    flour.refresh_from_db()
    assert item.quantity == Decimal("1.500")
    assert item.unit_code == "g"
    assert flour.name == "Mąka żytnia"
    assert flour.normalized_name == "maka zytnia"
    assert InventoryItem.objects.count() == 1
    assert Product.objects.filter(household=household).count() == 1


def test_item_edit_rejects_rename_to_existing_product_name(
    api_client: APIClient, ala: User, household: Household, flour: Product
) -> None:
    Product.objects.create(
        household=household,
        name="Cukier",
        normalized_name="cukier",
        default_unit_code="kg",
        is_food=True,
    )
    item = InventoryItem.objects.create(product=flour, unit_code="kg", quantity=Decimal("2.000"))
    api_client.force_login(ala)

    response = api_client.patch(
        f"/api/inventory/{item.pk}/", {"product_name": "cukier"}, format="json"
    )

    assert response.status_code == 400
    assert response.data["code"] == "duplicate_product"
    flour.refresh_from_db()
    assert flour.name == "Mąka pszenna"


def test_item_edit_rejects_unknown_unit(
    api_client: APIClient, ala: User, household: Household, flour: Product
) -> None:
    item = InventoryItem.objects.create(product=flour, unit_code="kg", quantity=Decimal("2.000"))
    api_client.force_login(ala)

    response = api_client.patch(
        f"/api/inventory/{item.pk}/", {"unit_code": "beczka"}, format="json"
    )

    assert response.status_code == 400
    assert response.data["code"] == "measurement_unit_not_found"
    item.refresh_from_db()
    assert item.unit_code == "kg"


def test_item_edit_is_denied_for_non_member(
    api_client: APIClient, ola: User, household: Household, flour: Product
) -> None:
    item = InventoryItem.objects.create(product=flour, unit_code="kg", quantity=Decimal("2.000"))
    api_client.force_login(ola)

    response = api_client.patch(
        f"/api/inventory/{item.pk}/", {"product_name": "Cukier"}, format="json"
    )

    assert response.status_code == 403
    assert response.data["code"] == "not_a_household_member"
    flour.refresh_from_db()
    assert flour.name == "Mąka pszenna"


def test_item_edit_of_another_household_item_is_rejected(
    api_client: APIClient, ola: User, household: Household, flour: Product
) -> None:
    own = Household.objects.create(name="Dom Oli")
    HouseholdMembership.objects.create(household=own, user=ola)
    item = InventoryItem.objects.create(product=flour, unit_code="kg", quantity=Decimal("2.000"))
    api_client.force_login(ola)

    response = api_client.patch(f"/api/inventory/{item.pk}/", {"quantity": "5"}, format="json")

    assert response.status_code == 403
    assert response.data["code"] == "not_a_household_member"
    item.refresh_from_db()
    assert item.quantity == Decimal("2.000")
