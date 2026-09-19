from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from households.models import Household, Product
from inventory.models import InventoryItem
from recipes.models import Recipe

pytestmark = pytest.mark.django_db


def _add_inventory(
    api_client: APIClient, household: Household, product: Product, quantity: str, unit: str
) -> int:
    response = api_client.post(
        "/api/inventory/",
        {
            "household_id": household.pk,
            "product_id": product.pk,
            "quantity": quantity,
            "unit_code": unit,
        },
        format="json",
    )
    assert response.status_code == 201, response.data
    item_id = response.data["id"]
    assert isinstance(item_id, int)
    return item_id


def _primary_list_id(api_client: APIClient, household: Household) -> int:
    response = api_client.get("/api/shopping/lists/", {"household_id": household.pk})
    assert response.status_code == 200, response.data
    primary = [item for item in response.data if item["is_primary"]]
    assert len(primary) == 1
    list_id = primary[0]["id"]
    assert isinstance(list_id, int)
    return list_id


def test_scenario_a_inventory_to_suggestion_to_shopping_to_inventory(
    api_client: APIClient,
    ala: User,
    household_a: Household,
    flour: Product,
    sugar: Product,
    pancakes: Recipe,
) -> None:
    api_client.force_login(ala)

    _add_inventory(api_client, household_a, flour, "0.200", "kg")

    suggestions = api_client.get("/api/recipes/suggestions/", {"household_id": household_a.pk})
    assert suggestions.status_code == 200, suggestions.data
    suggestion = next(item for item in suggestions.data if item["recipe_id"] == pancakes.pk)
    assert suggestion["available_item_count"] == 0
    assert suggestion["missing_item_count"] == 2

    missing = api_client.get(
        f"/api/recipes/{pancakes.pk}/missing-items/",
        {"household_id": household_a.pk, "servings": 4},
    )
    assert missing.status_code == 200, missing.data
    missing_by_name = {item["name"]: item for item in missing.data}
    assert Decimal(missing_by_name["Mąka pszenna"]["amount"]) == Decimal("300.000")
    assert missing_by_name["Mąka pszenna"]["unit_code"] == "g"
    assert Decimal(missing_by_name["Cukier"]["amount"]) == Decimal("100.000")

    list_id = _primary_list_id(api_client, household_a)
    added = api_client.post(
        f"/api/shopping/lists/{list_id}/items/from-recipe/",
        {"recipe_id": pancakes.pk, "servings": 4},
        format="json",
    )
    assert added.status_code == 200, added.data

    flour_before = InventoryItem.objects.get(household=household_a, product=flour)
    assert flour_before.quantity == Decimal("0.200")

    items = api_client.get(f"/api/shopping/lists/{list_id}/items/")
    sugar_item = next(item for item in items.data if item["product_name"] == "Cukier")

    bought = api_client.post(f"/api/shopping/items/{sugar_item['id']}/buy/")
    assert bought.status_code == 204, bought.data

    stored_sugar = InventoryItem.objects.get(household=household_a, product=sugar)
    assert stored_sugar.quantity == Decimal("100.000")
    assert stored_sugar.unit_code == "g"


def test_scenario_c_household_isolation_blocks_foreign_identifiers(
    api_client: APIClient,
    ala: User,
    ola: User,
    household_a: Household,
    household_b: Household,
    flour: Product,
    foreign_flour: Product,
    pancakes: Recipe,
) -> None:
    api_client.force_login(ola)
    foreign_list_id = _primary_list_id(api_client, household_b)
    foreign_item = api_client.post(
        f"/api/shopping/lists/{foreign_list_id}/items/",
        {"product_id": foreign_flour.pk, "quantity": "1.000", "unit_code": "kg"},
        format="json",
    )
    assert foreign_item.status_code == 201, foreign_item.data
    foreign_item_id = foreign_item.data["id"]
    api_client.logout()

    api_client.force_login(ala)

    assert (
        api_client.get("/api/inventory/", {"household_id": household_b.pk}).data["code"]
        == "not_a_household_member"
    )
    assert (
        api_client.post(
            "/api/inventory/",
            {
                "household_id": household_b.pk,
                "product_id": flour.pk,
                "quantity": "1.000",
                "unit_code": "kg",
            },
            format="json",
        ).data["code"]
        == "not_a_household_member"
    )
    assert (
        api_client.get("/api/products/", {"household_id": household_b.pk}).data["code"]
        == "not_a_household_member"
    )
    assert (
        api_client.get("/api/recipes/suggestions/", {"household_id": household_b.pk}).data["code"]
        == "not_a_household_member"
    )
    assert (
        api_client.get(
            f"/api/recipes/{pancakes.pk}/missing-items/",
            {"household_id": household_b.pk, "servings": 4},
        ).data["code"]
        == "not_a_household_member"
    )
    assert (
        api_client.get("/api/shopping/lists/", {"household_id": household_b.pk}).data["code"]
        == "not_a_household_member"
    )
    assert (
        api_client.get(f"/api/shopping/lists/{foreign_list_id}/items/").data["code"]
        == "not_a_household_member"
    )
    assert (
        api_client.post(f"/api/shopping/items/{foreign_item_id}/buy/").data["code"]
        == "not_a_household_member"
    )
    assert (
        api_client.delete(f"/api/shopping/items/{foreign_item_id}/").data["code"]
        == "not_a_household_member"
    )

    assert not InventoryItem.objects.filter(household=household_b).exists()


def test_a_foreign_product_cannot_be_attached_to_an_own_list(
    api_client: APIClient,
    ala: User,
    household_a: Household,
    household_b: Household,
    foreign_flour: Product,
) -> None:
    api_client.force_login(ala)
    list_id = _primary_list_id(api_client, household_a)

    response = api_client.post(
        f"/api/shopping/lists/{list_id}/items/",
        {"product_id": foreign_flour.pk, "quantity": "1.000", "unit_code": "kg"},
        format="json",
    )

    assert response.status_code == 400
    assert response.data["code"] == "product_not_found"


def test_a_foreign_product_cannot_be_added_to_an_own_inventory(
    api_client: APIClient,
    ala: User,
    household_a: Household,
    household_b: Household,
    foreign_flour: Product,
) -> None:
    api_client.force_login(ala)

    response = api_client.post(
        "/api/inventory/",
        {
            "household_id": household_a.pk,
            "product_id": foreign_flour.pk,
            "quantity": "1.000",
            "unit_code": "kg",
        },
        format="json",
    )

    assert response.status_code == 400
    assert response.data["code"] == "product_not_found"


def test_scenario_d_repeated_calculations_are_idempotent(
    api_client: APIClient,
    ala: User,
    household_a: Household,
    flour: Product,
    sugar: Product,
    pancakes: Recipe,
) -> None:
    api_client.force_login(ala)
    item_id = _add_inventory(api_client, household_a, flour, "0.200", "kg")
    InventoryItem.objects.filter(pk=item_id).update(minimum_quantity=Decimal("1.000"))

    list_id = _primary_list_id(api_client, household_a)

    first_recipe_run = api_client.post(
        f"/api/shopping/lists/{list_id}/items/from-recipe/",
        {"recipe_id": pancakes.pk, "servings": 4},
        format="json",
    )
    second_recipe_run = api_client.post(
        f"/api/shopping/lists/{list_id}/items/from-recipe/",
        {"recipe_id": pancakes.pk, "servings": 4},
        format="json",
    )
    assert first_recipe_run.status_code == 200
    assert second_recipe_run.status_code == 200
    assert first_recipe_run.data == second_recipe_run.data

    first_sync = api_client.post(f"/api/shopping/lists/{list_id}/synchronize-minimum-stock/")
    second_sync = api_client.post(f"/api/shopping/lists/{list_id}/synchronize-minimum-stock/")
    assert first_sync.status_code == 200, first_sync.data
    assert first_sync.data == second_sync.data

    items = api_client.get(f"/api/shopping/lists/{list_id}/items/")
    product_ids = [item["product_id"] for item in items.data]
    assert len(product_ids) == len(set(product_ids))
    assert Product.objects.filter(household=household_a).count() == 2


def test_recipe_fully_covered_by_inventory_has_no_missing_items(
    api_client: APIClient,
    ala: User,
    household_a: Household,
    flour: Product,
    sugar: Product,
    pancakes: Recipe,
) -> None:
    api_client.force_login(ala)
    _add_inventory(api_client, household_a, flour, "1.000", "kg")
    _add_inventory(api_client, household_a, sugar, "1.000", "kg")

    suggestions = api_client.get("/api/recipes/suggestions/", {"household_id": household_a.pk})
    suggestion = next(item for item in suggestions.data if item["recipe_id"] == pancakes.pk)

    assert suggestion["available_item_count"] == 2
    assert suggestion["missing_item_count"] == 0
    assert suggestion["missing_items"] == []


def test_a_more_specific_product_name_does_not_satisfy_a_recipe_requirement(
    api_client: APIClient,
    ala: User,
    household_a: Household,
    pancakes: Recipe,
) -> None:
    api_client.force_login(ala)
    specific = Product.objects.create(
        household=household_a,
        name="Mąka pszenna typ 500",
        normalized_name="maka pszenna typ 500",
        default_unit_code="kg",
        is_food=True,
    )
    _add_inventory(api_client, household_a, specific, "1.000", "kg")

    missing = api_client.get(
        f"/api/recipes/{pancakes.pk}/missing-items/",
        {"household_id": household_a.pk, "servings": 4},
    )

    assert {item["name"] for item in missing.data} == {"Mąka pszenna", "Cukier"}


def test_purchasing_locks_the_inventory_row_against_concurrent_updates(
    api_client: APIClient,
    ala: User,
    household_a: Household,
    sugar: Product,
) -> None:
    api_client.force_login(ala)
    _add_inventory(api_client, household_a, sugar, "0.500", "kg")
    list_id = _primary_list_id(api_client, household_a)
    item = api_client.post(
        f"/api/shopping/lists/{list_id}/items/",
        {"product_id": sugar.pk, "quantity": "0.250", "unit_code": "kg"},
        format="json",
    )
    assert item.status_code == 201, item.data

    with CaptureQueriesContext(connection) as captured:
        bought = api_client.post(f"/api/shopping/items/{item.data['id']}/buy/")

    assert bought.status_code == 204, bought.data
    assert any("FOR UPDATE" in query["sql"] for query in captured.captured_queries)
    assert InventoryItem.objects.get(household=household_a, product=sugar).quantity == Decimal(
        "0.750"
    )


def test_scenario_b_preparation_consumes_inventory_exactly_once(
    api_client: APIClient,
    ala: User,
    household_a: Household,
    flour: Product,
    sugar: Product,
    pancakes: Recipe,
) -> None:
    api_client.force_login(ala)
    _add_inventory(api_client, household_a, flour, "1.000", "kg")
    _add_inventory(api_client, household_a, sugar, "0.050", "kg")

    confirmed = api_client.post(
        f"/api/recipes/{pancakes.pk}/confirm-preparation/",
        {"household_id": household_a.pk, "servings": 4},
        format="json",
    )

    assert confirmed.status_code == 204, confirmed.data
    assert InventoryItem.objects.get(household=household_a, product=flour).quantity == Decimal(
        "0.500"
    )
    assert InventoryItem.objects.get(household=household_a, product=sugar).quantity == Decimal(
        "0.000"
    )


def test_scenario_b_preparation_is_rejected_for_non_members(
    api_client: APIClient,
    ala: User,
    household_b: Household,
    pancakes: Recipe,
) -> None:
    api_client.force_login(ala)

    response = api_client.post(
        f"/api/recipes/{pancakes.pk}/confirm-preparation/",
        {"household_id": household_b.pk, "servings": 4},
        format="json",
    )

    assert response.status_code == 403
    assert response.data["code"] == "not_a_household_member"


def test_scenario_b_minimum_stock_replenishes_the_primary_list_after_preparation(
    api_client: APIClient,
    ala: User,
    household_a: Household,
    flour: Product,
    sugar: Product,
    pancakes: Recipe,
) -> None:
    api_client.force_login(ala)
    flour_item_id = _add_inventory(api_client, household_a, flour, "1.000", "kg")
    _add_inventory(api_client, household_a, sugar, "1.000", "kg")
    InventoryItem.objects.filter(pk=flour_item_id).update(minimum_quantity=Decimal("0.800"))

    api_client.post(
        f"/api/recipes/{pancakes.pk}/confirm-preparation/",
        {"household_id": household_a.pk, "servings": 4},
        format="json",
    )

    list_id = _primary_list_id(api_client, household_a)
    synchronized = api_client.post(f"/api/shopping/lists/{list_id}/synchronize-minimum-stock/")

    assert synchronized.status_code == 200, synchronized.data
    flour_rows = [item for item in synchronized.data if item["product_id"] == flour.pk]
    assert len(flour_rows) == 1
    assert Decimal(flour_rows[0]["quantity"]) == Decimal("0.300")
