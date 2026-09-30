from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from rest_framework.test import APIClient

from catalog.models import Ingredient, Product
from config.composition import container
from households.models import Household
from recipes.models import RecipeCategory
from tests.factories import confirm_ingredient, make_household, make_ingredient, make_product

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
    household = make_household(member, "dom")
    return household.pk


@pytest.fixture
def eggs() -> Ingredient:
    return make_ingredient("jajko")


@pytest.fixture
def egg(member: User, household_id: int, eggs: Ingredient) -> Product:
    household = Household.objects.get(pk=household_id)
    product = make_product(household, "Jaja wiejskie", "g")
    confirm_ingredient(member, product, eggs)
    return product


def _stock(member: User, household_id: int, product: Product, grams: str) -> None:
    add_item = container().inventory.add_inventory_item
    add_item.execute(member.pk, household_id, product.pk, Decimal(grams), "g", None)


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
    assert response.data["category"] is None
    assert response.data["image_url"] is None
    assert response.data["steps"] == [{"position": 1, "text": "wbij jajka"}]
    assert response.data["ingredients"] == [
        {"name": "jajko", "ingredient_id": None, "quantity": "100.000", "unit_code": "g"}
    ]


def test_categories_are_listed_and_assigned_to_a_recipe(
    api_client: APIClient, member: User
) -> None:
    soups = RecipeCategory.objects.create(name="zupy")
    RecipeCategory.objects.create(name="desery")
    api_client.force_authenticate(member)

    listed = api_client.get("/api/recipes/categories/")
    created = api_client.post(
        "/api/recipes/", {**_recipe_body(), "category_id": soups.pk}, format="json"
    )

    assert [each["name"] for each in listed.data] == ["desery", "zupy"]
    assert created.data["category"] == {"id": soups.pk, "name": "zupy"}


def test_an_unknown_category_is_rejected(api_client: APIClient, member: User) -> None:
    api_client.force_authenticate(member)

    response = api_client.post(
        "/api/recipes/", {**_recipe_body(), "category_id": 999}, format="json"
    )

    assert response.status_code == 400
    assert response.data["code"] == "recipe_category_not_found"


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
    _stock(member, household_id, egg, "500")

    response = api_client.get(f"/api/recipes/suggestions/?household_id={household_id}")

    assert response.status_code == 200
    assert response.data == [
        {
            "recipe_id": recipe_id,
            "recipe_name": "omlet",
            "shortfall": {
                "missing_items": [],
                "required_item_count": 1,
                "available_item_count": 1,
                "unmeasured_ingredients": [],
                "is_ready": True,
            },
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
    _stock(member, household_id, egg, "150")

    response = api_client.get(
        f"/api/recipes/{recipe_id}/missing-items/?household_id={household_id}&servings=4"
    )

    assert response.status_code == 200
    assert response.data["missing_items"] == [
        {
            "name": "jajko",
            "ingredient_id": egg.ingredient_links.get().ingredient_id,
            "stocked_product_id": egg.pk,
            "amount": "50.000",
            "unit_code": "g",
        }
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
    _stock(member, household_id, egg, "500")

    response = api_client.post(
        f"/api/recipes/{recipe_id}/confirm-preparation/",
        {"household_id": household_id, "servings": 4},
        format="json",
    )

    assert response.status_code == 204
    get_inventory = container().inventory.get_household_inventory
    items = get_inventory.execute(member.pk, household_id)
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


def test_recipe_lines_name_their_ingredient_or_stay_unresolved(
    api_client: APIClient, member: User, eggs: Ingredient
) -> None:
    body = _recipe_body()
    body["ingredients"] = [
        {"name": "Jajko", "quantity": "2", "unit_code": "szt"},
        {"name": "szczypta miłości", "quantity": "1", "unit_code": "g"},
    ]
    api_client.force_authenticate(member)

    response = api_client.post("/api/recipes/", body, format="json")

    lines = {line["name"]: line["ingredient_id"] for line in response.data["ingredients"]}
    assert lines == {"Jajko": eggs.pk, "szczypta miłości": None}


def test_a_recipe_outlives_its_author(api_client: APIClient, member: User) -> None:
    recipe_id = _create_recipe(api_client, member)
    reader = User.objects.create_user(username="czytelnik", password="Ma-Kota-1234")

    member.delete()
    api_client.force_authenticate(reader)
    response = api_client.get(f"/api/recipes/{recipe_id}/")

    assert response.status_code == 200
    assert response.data["author_username"] is None


def test_recipe_nutrition_counts_tagged_mass_lines_per_serving(
    api_client: APIClient, member: User, eggs: Ingredient
) -> None:
    container().catalog.set_tag_calories.execute(eggs.pk, Decimal("143"))
    body = _recipe_body()
    body["ingredients"] = [
        {"name": "jajko", "quantity": "100", "unit_code": "g"},
        {"name": "mleko", "quantity": "50", "unit_code": "ml"},
        {"name": "szczypiorek", "quantity": "5", "unit_code": "g"},
    ]
    api_client.force_authenticate(member)
    created = api_client.post("/api/recipes/", body, format="json")

    response = api_client.get(f"/api/recipes/{created.data['id']}/nutrition/")

    assert response.status_code == 200
    assert response.data == {
        "total_kcal": "143.0",
        "kcal_per_serving": "71.5",
        "uncounted_ingredients": [
            {"name": "mleko", "reason": "not_by_mass"},
            {"name": "szczypiorek", "reason": "no_calories"},
        ],
    }


def test_nutrition_of_an_unknown_recipe_is_not_found(api_client: APIClient, member: User) -> None:
    api_client.force_authenticate(member)

    response = api_client.get("/api/recipes/9999/nutrition/")

    assert response.status_code == 404
