from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from households.composition import build_household_repository
from households.models import Product
from inventory.composition import build_add_inventory_item, build_get_household_inventory

pytestmark = [pytest.mark.django_db, pytest.mark.urls("recipes.tests.urls")]


@pytest.fixture
def api_client() -> APIClient:
    return APIClient()


@pytest.fixture
def member() -> User:
    return User.objects.create_user(username="ala", password="Ma-Kota-1234")


@pytest.fixture
def outsider() -> User:
    return User.objects.create_user(username="ola", password="Ma-Psa-1234")


@pytest.fixture
def household_id(member: User) -> int:
    return build_household_repository().create_household("dom", member.pk).id


@pytest.fixture
def egg(household_id: int) -> Product:
    return Product.objects.create(
        household_id=household_id,
        name="jajko",
        normalized_name="jajko",
        default_unit_code="g",
        is_food=True,
    )


def _recipe_body() -> dict[str, object]:
    return {
        "name": "omlet",
        "description": "prosty omlet",
        "servings": 2,
        "preparation_time_minutes": 5,
        "cooking_time_minutes": 7,
        "difficulty": "easy",
        "tag_names": ["szybkie"],
        "steps": [{"position": 1, "text": "wbij jajka"}],
        "ingredients": [{"name": "jajko", "quantity": "100.000", "unit_code": "g"}],
    }


def _create_recipe(api_client: APIClient, member: User) -> int:
    api_client.force_authenticate(member)
    response = api_client.post("/api/recipes/", _recipe_body(), format="json")
    assert response.status_code == 201, response.data
    return int(response.data["id"])


def test_anonymous_caller_is_rejected(api_client: APIClient) -> None:
    response = api_client.get("/api/recipes/")

    assert response.status_code == 403


def test_create_and_get_recipe(api_client: APIClient, member: User) -> None:
    recipe_id = _create_recipe(api_client, member)

    response = api_client.get(f"/api/recipes/{recipe_id}/")

    assert response.status_code == 200
    assert response.data["name"] == "omlet"
    assert response.data["tags"] == ["szybkie"]
    assert response.data["category_name"] is None
    assert response.data["image_url"] is None
    assert response.data["steps"] == [{"position": 1, "text": "wbij jajka"}]
    assert response.data["ingredients"] == [
        {"name": "jajko", "quantity": "100.000", "unit_code": "g"}
    ]


def test_list_recipes(api_client: APIClient, member: User) -> None:
    _create_recipe(api_client, member)

    response = api_client.get("/api/recipes/")

    assert response.status_code == 200
    assert len(response.data) == 1
    assert "steps" not in response.data[0]


def test_update_recipe_replaces_steps(api_client: APIClient, member: User) -> None:
    recipe_id = _create_recipe(api_client, member)
    body = _recipe_body()
    body["name"] = "omlet z serem"
    body["steps"] = [{"position": 1, "text": "wbij jajka"}, {"position": 2, "text": "dodaj ser"}]

    response = api_client.put(f"/api/recipes/{recipe_id}/", body, format="json")

    assert response.status_code == 200
    assert response.data["name"] == "omlet z serem"
    assert len(response.data["steps"]) == 2


def test_delete_recipe(api_client: APIClient, member: User) -> None:
    recipe_id = _create_recipe(api_client, member)

    assert api_client.delete(f"/api/recipes/{recipe_id}/").status_code == 204
    assert api_client.get(f"/api/recipes/{recipe_id}/").status_code == 404


def test_create_recipe_rejects_unknown_unit(api_client: APIClient, member: User) -> None:
    api_client.force_authenticate(member)
    body = _recipe_body()
    body["ingredients"] = [{"name": "jajko", "quantity": "1.000", "unit_code": "xyz"}]

    response = api_client.post("/api/recipes/", body, format="json")

    assert response.status_code == 400
    assert response.data["code"] == "measurement_unit_not_found"


def test_create_recipe_rejects_the_same_ingredient_twice(
    api_client: APIClient, member: User
) -> None:
    api_client.force_authenticate(member)
    body = _recipe_body()
    body["ingredients"] = [
        {"name": "jajko", "quantity": "1.000", "unit_code": "g"},
        {"name": "Jajko", "quantity": "2.000", "unit_code": "g"},
    ]

    response = api_client.post("/api/recipes/", body, format="json")

    assert response.status_code == 400
    assert response.data["code"] == "duplicate_recipe_ingredient"


def test_suggestions_report_stocked_recipe_as_complete(
    api_client: APIClient, member: User, egg: Product, household_id: int
) -> None:
    recipe_id = _create_recipe(api_client, member)
    build_add_inventory_item().execute(
        member.pk, household_id, egg.pk, Decimal("500"), "g", None, None
    )

    response = api_client.get(f"/api/recipes/suggestions/?household_id={household_id}")

    assert response.status_code == 200
    assert response.data == [
        {
            "recipe_id": recipe_id,
            "recipe_name": "omlet",
            "missing_items": [],
            "required_item_count": 1,
            "available_item_count": 1,
            "unmeasured_ingredients": [],
            "is_ready": True,
            "missing_item_count": 0,
        }
    ]


def test_suggestions_reject_non_member(
    api_client: APIClient, member: User, outsider: User, household_id: int
) -> None:
    api_client.force_authenticate(outsider)

    response = api_client.get(f"/api/recipes/suggestions/?household_id={household_id}")

    assert response.status_code == 403
    assert response.data["code"] == "not_a_household_member"


def test_missing_items_scale_with_servings(
    api_client: APIClient, member: User, egg: Product, household_id: int
) -> None:
    recipe_id = _create_recipe(api_client, member)
    build_add_inventory_item().execute(
        member.pk, household_id, egg.pk, Decimal("150"), "g", None, None
    )

    response = api_client.get(
        f"/api/recipes/{recipe_id}/missing-items/?household_id={household_id}&servings=4"
    )

    assert response.status_code == 200
    assert response.data["missing_items"] == [
        {"name": "jajko", "amount": "50.000", "unit_code": "g"}
    ]
    assert response.data["is_ready"] is False


def test_missing_items_reject_non_member(
    api_client: APIClient, member: User, outsider: User, household_id: int
) -> None:
    recipe_id = _create_recipe(api_client, member)
    api_client.force_authenticate(outsider)

    response = api_client.get(
        f"/api/recipes/{recipe_id}/missing-items/?household_id={household_id}&servings=2"
    )

    assert response.status_code == 403
    assert response.data["code"] == "not_a_household_member"


def test_missing_items_reject_zero_servings(
    api_client: APIClient, member: User, household_id: int
) -> None:
    recipe_id = _create_recipe(api_client, member)

    response = api_client.get(
        f"/api/recipes/{recipe_id}/missing-items/?household_id={household_id}&servings=0"
    )

    assert response.status_code == 400
    assert response.data["code"] == "invalid_servings"


def test_missing_items_reject_unknown_recipe(
    api_client: APIClient, member: User, household_id: int
) -> None:
    api_client.force_authenticate(member)

    response = api_client.get(
        f"/api/recipes/9999/missing-items/?household_id={household_id}&servings=2"
    )

    assert response.status_code == 404
    assert response.data["code"] == "recipe_not_found"


def test_confirm_preparation_consumes_inventory(
    api_client: APIClient, member: User, egg: Product, household_id: int
) -> None:
    recipe_id = _create_recipe(api_client, member)
    build_add_inventory_item().execute(
        member.pk, household_id, egg.pk, Decimal("500"), "g", None, None
    )

    response = api_client.post(
        f"/api/recipes/{recipe_id}/confirm-preparation/",
        {"household_id": household_id, "servings": 4},
        format="json",
    )

    assert response.status_code == 204
    items = build_get_household_inventory().execute(member.pk, household_id)
    assert items[0].quantity == Decimal("300.000")


def test_confirm_preparation_rejects_non_member(
    api_client: APIClient, member: User, outsider: User, household_id: int
) -> None:
    recipe_id = _create_recipe(api_client, member)
    api_client.force_authenticate(outsider)

    response = api_client.post(
        f"/api/recipes/{recipe_id}/confirm-preparation/",
        {"household_id": household_id, "servings": 2},
        format="json",
    )

    assert response.status_code == 403
    assert response.data["code"] == "not_a_household_member"
