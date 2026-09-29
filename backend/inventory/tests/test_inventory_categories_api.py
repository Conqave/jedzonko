import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from catalog.models import Product
from households.models import Household, HouseholdMembership
from inventory.models import InventoryCategory, InventoryItem

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
def other_household(ola: User) -> Household:
    created = Household.objects.create(name="Dom Oli")
    HouseholdMembership.objects.create(household=created, user=ola)
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


@pytest.fixture
def item(household: Household, flour: Product) -> InventoryItem:
    return InventoryItem.objects.create(product=flour, unit_code="kg", quantity="2.000")


def test_member_creates_and_lists_categories(
    api_client: APIClient, ala: User, household: Household
) -> None:
    api_client.force_login(ala)

    created = api_client.post(
        "/api/inventory/categories/",
        {"household_id": household.pk, "name": "Nabiał"},
        format="json",
    )

    assert created.status_code == 201
    assert created.data["name"] == "Nabiał"

    listed = api_client.get("/api/inventory/categories/", {"household_id": household.pk})

    assert listed.status_code == 200
    assert [row["name"] for row in listed.data] == ["Nabiał"]


def test_duplicate_category_is_rejected(
    api_client: APIClient, ala: User, household: Household
) -> None:
    api_client.force_login(ala)
    payload = {"household_id": household.pk, "name": "Nabiał"}
    api_client.post("/api/inventory/categories/", payload, format="json")

    response = api_client.post("/api/inventory/categories/", payload, format="json")

    assert response.status_code == 400
    assert response.data["code"] == "duplicate_inventory_category"


def test_listing_categories_is_denied_for_non_member(
    api_client: APIClient, ola: User, household: Household
) -> None:
    api_client.force_login(ola)

    response = api_client.get("/api/inventory/categories/", {"household_id": household.pk})

    assert response.status_code == 403
    assert response.data["code"] == "not_a_household_member"


def test_creating_a_category_is_denied_for_non_member(
    api_client: APIClient, ola: User, household: Household
) -> None:
    api_client.force_login(ola)

    response = api_client.post(
        "/api/inventory/categories/",
        {"household_id": household.pk, "name": "Nabiał"},
        format="json",
    )

    assert response.status_code == 403
    assert response.data["code"] == "not_a_household_member"


def test_member_assigns_and_clears_an_item_category(
    api_client: APIClient, ala: User, household: Household, item: InventoryItem
) -> None:
    api_client.force_login(ala)
    category = InventoryCategory.objects.create(household=household, name="Sypkie")

    assigned = api_client.put(
        f"/api/inventory/{item.pk}/category/", {"category_id": category.pk}, format="json"
    )

    assert assigned.status_code == 200
    assert assigned.data["category_id"] == category.pk
    assert assigned.data["category_name"] == "Sypkie"

    cleared = api_client.put(
        f"/api/inventory/{item.pk}/category/", {"category_id": None}, format="json"
    )

    assert cleared.status_code == 200
    assert cleared.data["category_id"] is None
    assert cleared.data["category_name"] is None


def test_item_cannot_be_assigned_a_category_from_another_household(
    api_client: APIClient,
    ala: User,
    household: Household,
    other_household: Household,
    item: InventoryItem,
) -> None:
    api_client.force_login(ala)
    foreign = InventoryCategory.objects.create(household=other_household, name="Obca")

    response = api_client.put(
        f"/api/inventory/{item.pk}/category/", {"category_id": foreign.pk}, format="json"
    )

    assert response.status_code == 400
    assert response.data["code"] == "inventory_category_not_found"


def test_changing_a_category_is_denied_for_non_member(
    api_client: APIClient, ola: User, household: Household, item: InventoryItem
) -> None:
    api_client.force_login(ola)

    response = api_client.put(
        f"/api/inventory/{item.pk}/category/", {"category_id": None}, format="json"
    )

    assert response.status_code == 403
    assert response.data["code"] == "not_a_household_member"


def test_item_is_added_with_a_category(
    api_client: APIClient, ala: User, household: Household, flour: Product
) -> None:
    api_client.force_login(ala)
    category = InventoryCategory.objects.create(household=household, name="Sypkie")

    response = api_client.post(
        "/api/inventory/",
        {
            "household_id": household.pk,
            "product_id": flour.pk,
            "quantity": "2.000",
            "unit_code": "kg",
            "category_id": category.pk,
        },
        format="json",
    )

    assert response.status_code == 201
    assert response.data["category_name"] == "Sypkie"


def test_item_cannot_be_added_with_a_foreign_category(
    api_client: APIClient,
    ala: User,
    household: Household,
    other_household: Household,
    flour: Product,
) -> None:
    api_client.force_login(ala)
    foreign = InventoryCategory.objects.create(household=other_household, name="Obca")

    response = api_client.post(
        "/api/inventory/",
        {
            "household_id": household.pk,
            "product_id": flour.pk,
            "quantity": "2.000",
            "unit_code": "kg",
            "category_id": foreign.pk,
        },
        format="json",
    )

    assert response.status_code == 400
    assert response.data["code"] == "inventory_category_not_found"


def test_member_renames_a_category(api_client: APIClient, ala: User, household: Household) -> None:
    category = InventoryCategory.objects.create(household=household, name="Spiżarnia")
    api_client.force_authenticate(ala)

    response = api_client.patch(
        f"/api/inventory/categories/{category.pk}/", {"name": "Szafka"}, format="json"
    )

    assert response.status_code == 200
    assert response.data == {"id": category.pk, "name": "Szafka"}


def test_renaming_to_a_taken_name_is_rejected(
    api_client: APIClient, ala: User, household: Household
) -> None:
    category = InventoryCategory.objects.create(household=household, name="Spiżarnia")
    InventoryCategory.objects.create(household=household, name="Lodówka")
    api_client.force_authenticate(ala)

    response = api_client.patch(
        f"/api/inventory/categories/{category.pk}/", {"name": "Lodówka"}, format="json"
    )

    assert response.status_code == 400
    assert response.data["code"] == "duplicate_inventory_category"


def test_deleting_a_category_leaves_its_items_uncategorised(
    api_client: APIClient, ala: User, household: Household, item: InventoryItem
) -> None:
    category = InventoryCategory.objects.create(household=household, name="Spiżarnia")
    item.category = category
    item.save()
    api_client.force_authenticate(ala)

    response = api_client.delete(f"/api/inventory/categories/{category.pk}/")

    item.refresh_from_db()
    assert response.status_code == 204
    assert item.category_id is None
    assert not InventoryCategory.objects.filter(pk=category.pk).exists()


def test_another_household_cannot_touch_a_category(
    api_client: APIClient, ola: User, household: Household, other_household: Household
) -> None:
    category = InventoryCategory.objects.create(household=household, name="Spiżarnia")
    api_client.force_authenticate(ola)

    renamed = api_client.patch(
        f"/api/inventory/categories/{category.pk}/", {"name": "Moja"}, format="json"
    )
    deleted = api_client.delete(f"/api/inventory/categories/{category.pk}/")

    assert (renamed.status_code, deleted.status_code) == (403, 403)
    assert InventoryCategory.objects.get(pk=category.pk).name == "Spiżarnia"


def test_an_unknown_category_is_not_found(api_client: APIClient, ala: User) -> None:
    api_client.force_authenticate(ala)

    response = api_client.delete("/api/inventory/categories/999/")

    assert response.data["code"] == "inventory_category_not_found"


def test_member_sets_and_clears_the_minimum_quantity(
    api_client: APIClient, ala: User, item: InventoryItem
) -> None:
    api_client.force_authenticate(ala)
    url = f"/api/inventory/{item.pk}/minimum/"

    raised = api_client.put(url, {"minimum_quantity": "5"}, format="json")
    cleared = api_client.put(url, {"minimum_quantity": None}, format="json")

    assert (raised.data["minimum_quantity"], raised.data["below_minimum"]) == ("5.000", True)
    assert (cleared.data["minimum_quantity"], cleared.data["below_minimum"]) == (None, False)


def test_a_negative_minimum_is_rejected(
    api_client: APIClient, ala: User, item: InventoryItem
) -> None:
    api_client.force_authenticate(ala)

    response = api_client.put(
        f"/api/inventory/{item.pk}/minimum/", {"minimum_quantity": "-1"}, format="json"
    )

    assert response.status_code == 400


def test_another_household_cannot_change_the_minimum(
    api_client: APIClient, ola: User, other_household: Household, item: InventoryItem
) -> None:
    api_client.force_authenticate(ola)

    response = api_client.put(
        f"/api/inventory/{item.pk}/minimum/", {"minimum_quantity": "1"}, format="json"
    )

    assert response.status_code == 403
