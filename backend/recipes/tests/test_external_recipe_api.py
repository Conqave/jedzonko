from collections.abc import Callable, Iterator
from contextlib import contextmanager
from decimal import Decimal
from pathlib import Path

import httpx
import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from households.models import Household, HouseholdMembership, IngredientTag, Product, ProductTag
from inventory.models import InventoryItem
from recipes.application.ports.recipe_source import RecipeSource
from recipes.infrastructure.providers.ania_gotuje.provider import AniaGotujeProvider
from recipes.models import Recipe, RecipeIngredient
from recipes.presentation import external_views

pytestmark = [pytest.mark.django_db, pytest.mark.urls("recipes.tests.urls")]

FIXTURES = Path(__file__).parent / "fixtures"
NALESNIKI = (FIXTURES / "ania_post_nalesniki.json").read_text(encoding="utf-8")
SEARCH = (FIXTURES / "ania_search_nalesniki.json").read_text(encoding="utf-8")
SLUG = "jak-zrobic-ciasto-na-nalesniki"


@pytest.fixture
def user() -> User:
    return User.objects.create_user(username="ala", password="Ma-Kota-1234")


@pytest.fixture
def api_client(user: User) -> APIClient:
    client = APIClient()
    client.force_authenticate(user)
    return client


@pytest.fixture
def household(user: User) -> Household:
    household = Household.objects.create(name="Dom")
    HouseholdMembership.objects.create(household=household, user=user)
    product = Product.objects.create(
        household=household,
        name="Jaja ściółkowe (opakowanie)",
        normalized_name="jaja sciolkowe (opakowanie)",
        default_unit_code="opak",
        is_food=True,
    )
    tag = IngredientTag.objects.create(name="jajko", normalized_name="jajko")
    ProductTag.objects.create(product=product, ingredient_tag=tag, is_verified=True)
    InventoryItem.objects.create(
        household=household, product=product, unit_code="opak", quantity=Decimal("1.000")
    )
    return household


def install_source(monkeypatch: pytest.MonkeyPatch, status_code: int, text: str) -> None:
    def handle_request(request: httpx.Request) -> httpx.Response:
        return httpx.Response(
            status_code, text=text, headers={"Content-Type": "application/json"}, request=request
        )

    @contextmanager
    def open_source() -> Iterator[RecipeSource]:
        yield AniaGotujeProvider(httpx.Client(transport=httpx.MockTransport(handle_request)))

    monkeypatch.setattr(external_views, "open_recipe_source", open_source)


def test_external_recipe_is_returned_with_attribution_and_not_stored(
    api_client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_source(monkeypatch, 200, NALESNIKI)
    recipe_count = Recipe.objects.count()
    ingredient_count = RecipeIngredient.objects.count()

    response = api_client.get(f"/api/recipes/external/{SLUG}/")

    assert response.status_code == 200
    assert response.data["source_name"] == "Ania Gotuje"
    assert response.data["source_url"] == f"https://aniagotuje.pl/przepis/{SLUG}"
    assert response.data["reference"] == SLUG
    assert response.data["name"] == "Naleśniki"
    assert response.data["preparation_time_minutes"] == 5
    assert response.data["cooking_time_minutes"] == 25
    assert response.data["steps"]
    assert len(response.data["ingredients"]) == 6
    assert Recipe.objects.count() == recipe_count
    assert RecipeIngredient.objects.count() == ingredient_count


def test_external_search_is_refused_outside_the_household(
    api_client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_source(monkeypatch, 200, SEARCH)

    response = api_client.get("/api/recipes/external/", {"household_id": "9999"})

    assert response.status_code == 403
    assert response.data["code"] == "not_a_household_member"


def test_unknown_external_recipe_is_reported_as_not_found(
    api_client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_source(monkeypatch, 404, "")

    response = api_client.get("/api/recipes/external/nie-ma-takiego/")

    assert response.status_code == 404
    assert response.data["code"] == "external_recipe_not_found"


def test_unavailable_source_is_reported_as_service_unavailable(
    api_client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_source(monkeypatch, 503, "")

    response = api_client.get(f"/api/recipes/external/{SLUG}/")

    assert response.status_code == 503
    assert response.data["code"] == "recipe_source_unavailable"


def test_unexpected_source_payload_is_reported_as_a_bad_gateway(
    api_client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_source(monkeypatch, 200, "<html>nope</html>")

    response = api_client.get(f"/api/recipes/external/{SLUG}/")

    assert response.status_code == 502
    assert response.data["code"] == "recipe_source_contract_invalid"


def test_external_search_returns_a_mapped_page_without_storing_anything(
    api_client: APIClient, household: Household, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_source(monkeypatch, 200, SEARCH)
    recipe_count = Recipe.objects.count()

    response = api_client.get(
        "/api/recipes/external/",
        {"query": "naleśniki", "page_size": "3", "household_id": str(household.pk)},
    )

    assert response.status_code == 200
    assert response.data["total_count"] == 252
    assert len(response.data["recipes"]) == 3
    assert response.data["recipes"][0]["source_name"] == "Ania Gotuje"
    assert response.data["recipes"][0]["source_url"].startswith("https://aniagotuje.pl/przepis/")
    assert response.data["recipes"][0]["matched_product_names"] == ["Jaja ściółkowe (opakowanie)"]
    assert response.data["recipes"][0]["matched_product_count"] == 1
    assert Recipe.objects.count() == recipe_count


def test_external_suggestions_require_household_membership(
    api_client: APIClient, monkeypatch: pytest.MonkeyPatch
) -> None:
    install_source(monkeypatch, 200, SEARCH)

    response = api_client.get("/api/recipes/external/suggestions/", {"household_id": "9999"})

    assert response.status_code == 403
    assert response.data["code"] == "not_a_household_member"
