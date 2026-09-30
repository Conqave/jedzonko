from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.db import connection
from django.test.utils import CaptureQueriesContext
from rest_framework.test import APIClient

from catalog.models import Ingredient, Product
from config.composition import container
from households.models import Household
from inventory.models import InventoryItem
from tests.factories import confirm_ingredient, make_ingredient, make_product

pytestmark = pytest.mark.django_db


@pytest.fixture
def api_client(ala: User) -> APIClient:
    client = APIClient()
    client.force_login(ala)
    return client


@pytest.fixture
def household(household_a: Household) -> Household:
    return household_a


def _tag(name: str, kcal_per_100g: str | None) -> Ingredient:
    ingredient = make_ingredient(name)
    if kcal_per_100g is not None:
        container().catalog.set_tag_calories.execute(ingredient.pk, Decimal(kcal_per_100g))
    return ingredient


def _stock(product: Product, quantity: str, unit_code: str) -> InventoryItem:
    return InventoryItem.objects.create(
        product=product, quantity=Decimal(quantity), unit_code=unit_code
    )


def _calories_by_product(api_client: APIClient, household: Household) -> dict[str, object]:
    response = api_client.get("/api/inventory/", {"household_id": household.pk})
    assert response.status_code == 200
    return {item["product_name"]: item["calories"] for item in response.data}


def test_the_pantry_counts_the_stocked_amount_from_the_single_tag(
    api_client: APIClient, ala: User, household: Household
) -> None:
    flour = make_product(household, "Mąka pszenna", "kg")
    confirm_ingredient(ala, flour, _tag("mąka", "364"))
    _stock(flour, "2", "kg")

    calories = _calories_by_product(api_client, household)

    assert calories["Mąka pszenna"] == {
        "kcal": "7280.0",
        "kcal_per_100g": "364.0",
        "is_estimate": False,
        "uncounted_reason": None,
    }


def test_the_pantry_says_why_it_cannot_count_an_item(
    api_client: APIClient, ala: User, household: Household
) -> None:
    salt = make_product(household, "Sól", "g")
    mix = make_product(household, "Mieszanka studencka", "g")
    water = make_product(household, "Woda", "l")
    confirm_ingredient(ala, mix, _tag("orzechy", "650"))
    confirm_ingredient(ala, mix, _tag("rodzynki", "300"))
    confirm_ingredient(ala, water, _tag("woda", None))
    for product in (salt, mix, water):
        _stock(product, "1", product.default_unit_code)

    calories = _calories_by_product(api_client, household)

    assert calories["Sól"] == {
        "kcal": None,
        "kcal_per_100g": None,
        "is_estimate": False,
        "uncounted_reason": "no_tag",
    }
    assert calories["Mieszanka studencka"] == {
        "kcal": None,
        "kcal_per_100g": None,
        "is_estimate": False,
        "uncounted_reason": "several_tags",
    }
    assert calories["Woda"] == {
        "kcal": None,
        "kcal_per_100g": None,
        "is_estimate": False,
        "uncounted_reason": "no_calories",
    }


def test_changing_the_amount_returns_the_new_calories(
    api_client: APIClient, ala: User, household: Household
) -> None:
    flour = make_product(household, "Mąka pszenna", "kg")
    confirm_ingredient(ala, flour, _tag("mąka", "364"))
    item = _stock(flour, "2", "kg")

    response = api_client.patch(f"/api/inventory/{item.pk}/", {"quantity": "500", "unit_code": "g"})

    assert response.status_code == 200
    assert response.data["calories"]["kcal"] == "1820.0"


def test_the_pantry_reads_calories_in_a_fixed_number_of_queries(
    api_client: APIClient, ala: User, household: Household
) -> None:
    flour = make_product(household, "Mąka pszenna", "kg")
    confirm_ingredient(ala, flour, _tag("mąka", "364"))
    _stock(flour, "1", "kg")
    with CaptureQueriesContext(connection) as single:
        _calories_by_product(api_client, household)
    for name in ("Cukier", "Ryż", "Kasza"):
        product = make_product(household, name, "kg")
        confirm_ingredient(ala, product, _tag(name.lower(), "350"))
        _stock(product, "1", "kg")

    with CaptureQueriesContext(connection) as several:
        _calories_by_product(api_client, household)

    assert len(several.captured_queries) == len(single.captured_queries)
