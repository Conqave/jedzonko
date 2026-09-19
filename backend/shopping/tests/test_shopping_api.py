from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.db import transaction
from django.db.utils import IntegrityError
from rest_framework.test import APIClient

from households.composition import build_household_access_policy
from households.models import Household, HouseholdMembership, Product
from inventory.models import InventoryItem
from shopping.application.use_cases.add_missing_recipe_items_to_shopping_list import (
    AddMissingRecipeItemsToShoppingList,
)
from shopping.composition import build_product_resolver, build_shopping_list_repository
from shopping.domain.missing_recipe_item import MissingRecipeItem
from shopping.models import (
    PrimaryShoppingList,
    PurchasedShoppingItem,
    ShoppingList,
    ShoppingListItem,
)
from shopping.presentation import views
from shopping.tests.fakes import FakeProductResolver, FakeRecipeRequirementReader

pytestmark = [pytest.mark.django_db, pytest.mark.urls("shopping.tests.urls")]


@pytest.fixture
def flour(household: Household) -> Product:
    return Product.objects.create(
        household=household,
        name="Mąka",
        normalized_name="maka",
        default_unit_code="g",
        is_food=True,
    )


@pytest.fixture
def foreign_flour(other_household: Household) -> Product:
    return Product.objects.create(
        household=other_household,
        name="Mąka",
        normalized_name="maka",
        default_unit_code="g",
        is_food=True,
    )


@pytest.fixture
def member() -> User:
    return User.objects.create_user(username="member", password="secret-pass-1")


@pytest.fixture
def outsider() -> User:
    return User.objects.create_user(username="outsider", password="secret-pass-2")


@pytest.fixture
def household(member: User) -> Household:
    created = Household.objects.create(name="Dom")
    HouseholdMembership.objects.create(household=created, user=member)
    return created


@pytest.fixture
def other_household(outsider: User) -> Household:
    created = Household.objects.create(name="Obcy dom")
    HouseholdMembership.objects.create(household=created, user=outsider)
    return created


@pytest.fixture
def member_client(member: User) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=member)
    return client


@pytest.fixture
def outsider_client(outsider: User) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=outsider)
    return client


def _primary_list_id(client: APIClient, household: Household) -> int:
    response = client.get("/api/shopping/lists/", {"household_id": household.pk})
    assert response.status_code == 200
    return int(response.json()[0]["id"])


def test_anonymous_caller_is_rejected() -> None:
    client = APIClient()
    assert client.get("/api/shopping/lists/?household_id=1").status_code == 403
    assert client.post("/api/shopping/lists/", {}, format="json").status_code == 403
    assert client.get("/api/shopping/lists/1/items/").status_code == 403
    assert client.post("/api/shopping/lists/1/items/", {}, format="json").status_code == 403
    assert client.post("/api/shopping/items/1/buy/").status_code == 403
    assert client.delete("/api/shopping/items/1/").status_code == 403


def test_list_endpoint_creates_the_primary_list(
    member_client: APIClient, household: Household
) -> None:
    response = member_client.get("/api/shopping/lists/", {"household_id": household.pk})

    assert response.status_code == 200
    assert response.json() == [
        {
            "id": ShoppingList.objects.get(household=household).pk,
            "name": "Lista zakupów",
            "is_primary": True,
            "item_count": 0,
        }
    ]
    member_client.get("/api/shopping/lists/", {"household_id": household.pk})
    assert ShoppingList.objects.filter(household=household).count() == 1
    assert PrimaryShoppingList.objects.filter(household=household).count() == 1


def test_non_member_cannot_read_lists(outsider_client: APIClient, household: Household) -> None:
    response = outsider_client.get("/api/shopping/lists/", {"household_id": household.pk})

    assert response.status_code == 403
    assert response.json()["code"] == "not_a_household_member"


def test_create_named_list(member_client: APIClient, household: Household) -> None:
    response = member_client.post(
        "/api/shopping/lists/", {"household_id": household.pk, "name": "Weekend"}, format="json"
    )

    assert response.status_code == 201
    assert response.json()["name"] == "Weekend"
    assert response.json()["is_primary"] is False


def test_non_member_cannot_create_list(outsider_client: APIClient, household: Household) -> None:
    response = outsider_client.post(
        "/api/shopping/lists/", {"household_id": household.pk, "name": "Weekend"}, format="json"
    )

    assert response.status_code == 403
    assert response.json()["code"] == "not_a_household_member"


def test_unknown_list_returns_shopping_list_not_found(member_client: APIClient) -> None:
    response = member_client.get("/api/shopping/lists/9999/items/")

    assert response.status_code == 404
    assert response.json()["code"] == "shopping_list_not_found"


def test_member_of_other_household_cannot_read_items(
    member_client: APIClient, outsider_client: APIClient, other_household: Household
) -> None:
    list_id = _primary_list_id(outsider_client, other_household)

    response = member_client.get(f"/api/shopping/lists/{list_id}/items/")

    assert response.status_code == 403
    assert response.json()["code"] == "not_a_household_member"


def test_member_of_other_household_cannot_mutate_items(
    member_client: APIClient,
    outsider_client: APIClient,
    other_household: Household,
    foreign_flour: Product,
) -> None:
    list_id = _primary_list_id(outsider_client, other_household)
    created = outsider_client.post(
        f"/api/shopping/lists/{list_id}/items/",
        {"product_id": foreign_flour.pk, "quantity": "100.000", "unit_code": "g"},
        format="json",
    )
    item_id = created.json()["id"]

    assert (
        member_client.post(
            f"/api/shopping/lists/{list_id}/items/",
            {"free_text": "Ręczniki", "quantity": "1.000"},
            format="json",
        ).status_code
        == 403
    )
    assert member_client.post(f"/api/shopping/items/{item_id}/buy/").status_code == 403
    assert member_client.delete(f"/api/shopping/items/{item_id}/").status_code == 403
    assert (
        member_client.post(f"/api/shopping/lists/{list_id}/synchronize-minimum-stock/").status_code
        == 403
    )


def test_add_product_item(member_client: APIClient, household: Household, flour: Product) -> None:
    list_id = _primary_list_id(member_client, household)

    response = member_client.post(
        f"/api/shopping/lists/{list_id}/items/",
        {"product_id": flour.pk, "quantity": "250.000", "unit_code": "g"},
        format="json",
    )

    assert response.status_code == 201
    body = response.json()
    assert body["product_id"] == flour.pk
    assert body["product_name"] == "Mąka"
    assert body["free_text"] is None
    assert body["quantity"] == "250.000"
    assert body["unit_code"] == "g"
    assert body["is_purchased"] is False


def test_item_with_both_product_and_free_text_is_rejected(
    member_client: APIClient, household: Household, flour: Product
) -> None:
    list_id = _primary_list_id(member_client, household)

    response = member_client.post(
        f"/api/shopping/lists/{list_id}/items/",
        {
            "product_id": flour.pk,
            "free_text": "Ręczniki",
            "quantity": "1.000",
            "unit_code": "g",
        },
        format="json",
    )

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_shopping_item"


def test_item_with_neither_product_nor_free_text_is_rejected(
    member_client: APIClient, household: Household
) -> None:
    list_id = _primary_list_id(member_client, household)

    response = member_client.post(
        f"/api/shopping/lists/{list_id}/items/", {"quantity": "1.000"}, format="json"
    )

    assert response.status_code == 400
    assert response.json()["code"] == "invalid_shopping_item"


def test_buying_adds_quantity_to_inventory(
    member_client: APIClient, household: Household, flour: Product
) -> None:
    list_id = _primary_list_id(member_client, household)
    created = member_client.post(
        f"/api/shopping/lists/{list_id}/items/",
        {"product_id": flour.pk, "quantity": "250.000", "unit_code": "g"},
        format="json",
    )
    item_id = created.json()["id"]

    response = member_client.post(f"/api/shopping/items/{item_id}/buy/")

    assert response.status_code == 204
    stored = InventoryItem.objects.get(household=household, product=flour)
    assert stored.quantity == Decimal("250.000")
    assert ShoppingListItem.objects.filter(pk=item_id).exists() is False
    assert PurchasedShoppingItem.objects.filter(shopping_list__household=household).count() == 1


def test_buying_twice_is_rejected(
    member_client: APIClient, household: Household, flour: Product
) -> None:
    list_id = _primary_list_id(member_client, household)
    created = member_client.post(
        f"/api/shopping/lists/{list_id}/items/",
        {"product_id": flour.pk, "quantity": "250.000", "unit_code": "g"},
        format="json",
    )
    item_id = created.json()["id"]
    member_client.post(f"/api/shopping/items/{item_id}/buy/")

    response = member_client.post(f"/api/shopping/items/{item_id}/buy/")

    assert response.status_code == 404
    assert response.json()["code"] == "shopping_item_not_found"
    assert InventoryItem.objects.get(household=household, product=flour).quantity == Decimal(
        "250.000"
    )


def test_delete_item(member_client: APIClient, household: Household, flour: Product) -> None:
    list_id = _primary_list_id(member_client, household)
    created = member_client.post(
        f"/api/shopping/lists/{list_id}/items/",
        {"product_id": flour.pk, "quantity": "250.000", "unit_code": "g"},
        format="json",
    )
    item_id = created.json()["id"]

    assert member_client.delete(f"/api/shopping/items/{item_id}/").status_code == 204
    assert member_client.delete(f"/api/shopping/items/{item_id}/").status_code == 404


def test_buy_unknown_item_returns_shopping_item_not_found(member_client: APIClient) -> None:
    response = member_client.post("/api/shopping/items/9999/buy/")

    assert response.status_code == 404
    assert response.json()["code"] == "shopping_item_not_found"


def test_from_recipe_is_idempotent(
    member_client: APIClient,
    household: Household,
    flour: Product,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    list_id = _primary_list_id(member_client, household)
    recipes = FakeRecipeRequirementReader(
        [
            MissingRecipeItem(
                name="Mąka",
                normalized_name="maka",
                amount=Decimal("300"),
                unit_code="g",
            )
        ]
    )

    def _build() -> AddMissingRecipeItemsToShoppingList:
        return AddMissingRecipeItemsToShoppingList(
            build_shopping_list_repository(),
            build_household_access_policy(),
            recipes,
            build_product_resolver(),
        )

    monkeypatch.setattr(views, "build_add_missing_recipe_items_to_shopping_list", _build)

    first = member_client.post(
        f"/api/shopping/lists/{list_id}/items/from-recipe/",
        {"recipe_id": 1, "servings": 4},
        format="json",
    )
    second = member_client.post(
        f"/api/shopping/lists/{list_id}/items/from-recipe/",
        {"recipe_id": 1, "servings": 4},
        format="json",
    )

    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json() == second.json()
    assert ShoppingListItem.objects.filter(shopping_list_id=list_id).count() == 1
    assert second.json()[0]["quantity"] == "300.000"


def test_synchronize_minimum_stock_is_idempotent(
    member_client: APIClient, household: Household, flour: Product
) -> None:
    list_id = _primary_list_id(member_client, household)
    InventoryItem.objects.create(
        household=household,
        product=flour,
        unit_code="g",
        quantity=Decimal("100"),
        minimum_quantity=Decimal("300"),
    )

    first = member_client.post(f"/api/shopping/lists/{list_id}/synchronize-minimum-stock/")
    second = member_client.post(f"/api/shopping/lists/{list_id}/synchronize-minimum-stock/")

    assert first.status_code == 200
    assert first.json() == second.json()
    assert ShoppingListItem.objects.filter(shopping_list_id=list_id).count() == 1
    assert second.json()[0]["quantity"] == "200.000"
    assert second.json()[0]["unit_code"] == "g"


def test_purchased_items_stay_visible_and_can_be_rebought(
    member_client: APIClient, household: Household, flour: Product
) -> None:
    list_id = _primary_list_id(member_client, household)
    first = member_client.post(
        f"/api/shopping/lists/{list_id}/items/",
        {"product_id": flour.pk, "quantity": "250.000", "unit_code": "g"},
        format="json",
    )
    member_client.post(f"/api/shopping/items/{first.json()['id']}/buy/")

    second = member_client.post(
        f"/api/shopping/lists/{list_id}/items/",
        {"product_id": flour.pk, "quantity": "100.000", "unit_code": "g"},
        format="json",
    )

    assert second.status_code == 201
    items = member_client.get(f"/api/shopping/lists/{list_id}/items/").json()
    assert [item["is_purchased"] for item in items] == [True, False]
    assert [item["quantity"] for item in items] == ["250.000", "100.000"]


def test_database_rejects_a_second_pending_row_for_the_same_product(
    household: Household, flour: Product
) -> None:
    shopping_list = ShoppingList.objects.create(household=household, name="Lista")
    ShoppingListItem.objects.create(
        shopping_list=shopping_list, product=flour, unit_code="g", quantity=Decimal("1.000")
    )

    with pytest.raises(IntegrityError), transaction.atomic():
        ShoppingListItem.objects.create(
            shopping_list=shopping_list, product=flour, unit_code="g", quantity=Decimal("2.000")
        )


def test_database_allows_several_pending_free_text_rows(
    household: Household,
) -> None:
    shopping_list = ShoppingList.objects.create(household=household, name="Lista")
    ShoppingListItem.objects.create(
        shopping_list=shopping_list, free_text="Ręczniki", quantity=Decimal("1.000")
    )
    ShoppingListItem.objects.create(
        shopping_list=shopping_list, free_text="Mydło", quantity=Decimal("1.000")
    )

    assert ShoppingListItem.objects.filter(shopping_list=shopping_list).count() == 2


def test_database_rejects_a_second_primary_list_for_one_household(
    household: Household,
) -> None:
    first = ShoppingList.objects.create(household=household, name="Lista")
    second = ShoppingList.objects.create(household=household, name="Inna")
    PrimaryShoppingList.objects.create(household=household, shopping_list=first)

    with pytest.raises(IntegrityError), transaction.atomic():
        PrimaryShoppingList.objects.create(household=household, shopping_list=second)


def test_database_rejects_one_list_being_primary_for_two_households(
    household: Household, other_household: Household
) -> None:
    shopping_list = ShoppingList.objects.create(household=household, name="Lista")
    PrimaryShoppingList.objects.create(household=household, shopping_list=shopping_list)

    with pytest.raises(IntegrityError), transaction.atomic():
        PrimaryShoppingList.objects.create(household=other_household, shopping_list=shopping_list)
