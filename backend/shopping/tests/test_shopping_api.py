from collections.abc import Callable, Iterator
from datetime import datetime
from decimal import Decimal

import pytest
from django.contrib.auth.models import User
from django.db import IntegrityError, transaction
from rest_framework.test import APIClient

from catalog.models import Ingredient, Product, ProductIngredient
from config.composition import container
from households.models import Household
from inventory.models import InventoryItem
from recipes.models import Recipe
from shopping.application.errors import TaggingUnavailableError
from shopping.application.ports.line_interpreter import LineInterpreter
from shopping.domain.line_meaning import LineMeaning
from shopping.models import ShoppingList, ShoppingListItem
from shopping.tests.fakes import FakeLineInterpreter
from tests.factories import (
    add_recipe_line,
    confirm_ingredient,
    make_household,
    make_ingredient,
    make_product,
)

pytestmark = pytest.mark.django_db


@pytest.fixture
def member_client(ala: User) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=ala)
    return client


@pytest.fixture
def outsider_client(ola: User) -> APIClient:
    client = APIClient()
    client.force_authenticate(user=ola)
    return client


@pytest.fixture
def home(ala: User) -> Household:
    return make_household(ala, "Dom")


@pytest.fixture
def flour(home: Household) -> Product:
    return make_product(home, "Mąka", "g")


def _primary_list_id(client: APIClient, household: Household) -> int:
    response = client.get("/api/shopping/lists/", {"household_id": household.pk})
    return int(response.data[0]["id"])


def _add(client: APIClient, list_id: int, body: dict[str, object]) -> dict[str, object]:
    response = client.post(f"/api/shopping/lists/{list_id}/items/", body, format="json")
    assert response.status_code == 201, response.data
    data: dict[str, object] = response.data
    return data


def test_anonymous_caller_is_rejected(api_client: APIClient) -> None:
    response = api_client.get("/api/shopping/lists/", {"household_id": 1})

    assert response.status_code == 403


def test_listing_shows_the_primary_list_without_creating_anything(
    member_client: APIClient, home: Household
) -> None:
    before = ShoppingList.objects.count()

    response = member_client.get("/api/shopping/lists/", {"household_id": home.pk})

    assert [(each["name"], each["is_primary"]) for each in response.data] == [
        ("Lista zakupów", True)
    ]
    assert ShoppingList.objects.count() == before


def test_non_member_cannot_read_lists(outsider_client: APIClient, home: Household) -> None:
    response = outsider_client.get("/api/shopping/lists/", {"household_id": home.pk})

    assert response.status_code == 403
    assert response.data["code"] == "not_a_household_member"


def test_member_creates_renames_and_deletes_a_list(
    member_client: APIClient, home: Household
) -> None:
    created = member_client.post(
        "/api/shopping/lists/", {"household_id": home.pk, "name": "Impreza"}, format="json"
    )
    list_id = created.data["id"]
    renamed = member_client.patch(
        f"/api/shopping/lists/{list_id}/", {"name": "Grill"}, format="json"
    )
    deleted = member_client.delete(f"/api/shopping/lists/{list_id}/")

    assert (created.status_code, renamed.data["name"], deleted.status_code) == (201, "Grill", 204)


def test_the_primary_list_cannot_be_deleted(member_client: APIClient, home: Household) -> None:
    list_id = _primary_list_id(member_client, home)

    response = member_client.delete(f"/api/shopping/lists/{list_id}/")

    assert response.status_code == 400
    assert response.data["code"] == "primary_shopping_list_cannot_be_deleted"


def test_an_outsider_cannot_touch_the_list(
    member_client: APIClient, outsider_client: APIClient, home: Household
) -> None:
    list_id = _primary_list_id(member_client, home)
    item = _add(member_client, list_id, {"free_text": "chleb", "quantity": "1"})

    read = outsider_client.get(f"/api/shopping/lists/{list_id}/items/")
    bought = outsider_client.post(f"/api/shopping/items/{item['id']}/purchase/")
    deleted = outsider_client.delete(f"/api/shopping/items/{item['id']}/")

    assert (read.status_code, bought.status_code, deleted.status_code) == (403, 403, 403)


def test_items_are_about_a_product_an_ingredient_or_text(
    member_client: APIClient, home: Household, flour: Product
) -> None:
    eggs = make_ingredient("Jajka")
    list_id = _primary_list_id(member_client, home)

    product = _add(
        member_client, list_id, {"product_id": flour.pk, "quantity": "500", "unit_code": "g"}
    )
    ingredient = _add(
        member_client, list_id, {"ingredient_id": eggs.pk, "quantity": "6", "unit_code": "szt"}
    )
    text = _add(member_client, list_id, {"free_text": "ręczniki", "quantity": "1"})

    assert (product["name"], product["product_id"]) == ("Mąka", flour.pk)
    assert (ingredient["name"], ingredient["ingredient_id"]) == ("Jajka", eggs.pk)
    assert (text["name"], text["unit_code"]) == ("ręczniki", None)


@pytest.mark.parametrize(
    "body",
    [
        {"product_id": 1, "free_text": "mąka", "quantity": "1", "unit_code": "g"},
        {"quantity": "1"},
        {"ingredient_id": 1, "quantity": "1"},
    ],
)
def test_an_ill_formed_item_is_rejected(
    member_client: APIClient, home: Household, body: dict[str, object]
) -> None:
    list_id = _primary_list_id(member_client, home)

    response = member_client.post(f"/api/shopping/lists/{list_id}/items/", body, format="json")

    assert response.status_code == 400


def test_a_product_of_another_household_is_rejected(
    member_client: APIClient, home: Household, ola: User
) -> None:
    other = make_household(ola, "Obcy dom")
    foreign = make_product(other, "Mąka", "g")
    list_id = _primary_list_id(member_client, home)

    response = member_client.post(
        f"/api/shopping/lists/{list_id}/items/",
        {"product_id": foreign.pk, "quantity": "1", "unit_code": "g"},
        format="json",
    )

    assert response.status_code == 400
    assert response.data["code"] == "product_not_found"


def test_buying_a_product_adds_it_to_the_pantry_and_keeps_it_visible(
    member_client: APIClient, home: Household, flour: Product
) -> None:
    list_id = _primary_list_id(member_client, home)
    item = _add(
        member_client, list_id, {"product_id": flour.pk, "quantity": "500", "unit_code": "g"}
    )

    bought = member_client.post(f"/api/shopping/items/{item['id']}/purchase/")
    again = member_client.post(f"/api/shopping/items/{item['id']}/purchase/")
    items = member_client.get(f"/api/shopping/lists/{list_id}/items/")

    assert (bought.status_code, again.status_code) == (204, 404)
    assert InventoryItem.objects.get(product=flour).quantity == Decimal("500.000")
    assert [(each["id"], each["status"]) for each in items.data] == [(item["id"], "purchased")]


def test_ticked_items_are_bought_together(
    member_client: APIClient, home: Household, flour: Product
) -> None:
    list_id = _primary_list_id(member_client, home)
    flour_item = _add(
        member_client, list_id, {"product_id": flour.pk, "quantity": "500", "unit_code": "g"}
    )
    bread = _add(member_client, list_id, {"free_text": "chleb", "quantity": "1"})
    url = f"/api/shopping/lists/{list_id}/purchase/"

    body = {"items": [{"item_id": flour_item["id"]}, {"item_id": bread["id"]}]}

    bought = member_client.post(url, body, format="json")
    again = member_client.post(url, {"items": [{"item_id": bread["id"]}]}, format="json")
    items = member_client.get(f"/api/shopping/lists/{list_id}/items/")

    assert (bought.status_code, again.status_code) == (204, 404)
    assert InventoryItem.objects.get(product=flour).quantity == Decimal("500.000")
    assert {each["status"] for each in items.data} == {"purchased"}


def test_ticked_items_are_deleted_together(
    member_client: APIClient, home: Household, flour: Product
) -> None:
    list_id = _primary_list_id(member_client, home)
    flour_item = _add(
        member_client, list_id, {"product_id": flour.pk, "quantity": "500", "unit_code": "g"}
    )
    bread = _add(member_client, list_id, {"free_text": "chleb", "quantity": "1"})
    milk = _add(member_client, list_id, {"free_text": "mleko", "quantity": "1"})
    url = f"/api/shopping/lists/{list_id}/item-deletion/"

    deleted = member_client.post(url, {"item_ids": [flour_item["id"], bread["id"]]}, format="json")
    again = member_client.post(url, {"item_ids": [bread["id"]]}, format="json")
    items = member_client.get(f"/api/shopping/lists/{list_id}/items/")

    assert (deleted.status_code, again.status_code) == (204, 404)
    assert [each["id"] for each in items.data] == [milk["id"]]


def test_deleting_ticked_items_is_all_or_nothing(member_client: APIClient, home: Household) -> None:
    list_id = _primary_list_id(member_client, home)
    bread = _add(member_client, list_id, {"free_text": "chleb", "quantity": "1"})
    other = member_client.post(
        "/api/shopping/lists/", {"household_id": home.pk, "name": "Impreza"}, format="json"
    )
    foreign = _add(member_client, other.data["id"], {"free_text": "chipsy", "quantity": "1"})
    url = f"/api/shopping/lists/{list_id}/item-deletion/"

    mixed = member_client.post(url, {"item_ids": [bread["id"], foreign["id"]]}, format="json")

    assert mixed.status_code == 404
    assert mixed.data["code"] == "shopping_item_not_found"
    assert ShoppingListItem.objects.filter(shopping_list__household=home).count() == 2


@pytest.mark.parametrize(
    "body", [{}, {"item_ids": []}, {"item_ids": [0]}, {"item_ids": [5, 5]}, {"item_ids": "5"}]
)
def test_an_ill_formed_deletion_is_rejected(
    member_client: APIClient, home: Household, body: dict[str, object]
) -> None:
    list_id = _primary_list_id(member_client, home)

    response = member_client.post(
        f"/api/shopping/lists/{list_id}/item-deletion/", body, format="json"
    )

    assert response.status_code == 400


def test_an_outsider_cannot_delete_ticked_items(
    member_client: APIClient, outsider_client: APIClient, home: Household
) -> None:
    list_id = _primary_list_id(member_client, home)
    bread = _add(member_client, list_id, {"free_text": "chleb", "quantity": "1"})

    response = outsider_client.post(
        f"/api/shopping/lists/{list_id}/item-deletion/", {"item_ids": [bread["id"]]}, format="json"
    )

    items = member_client.get(f"/api/shopping/lists/{list_id}/items/")

    assert response.status_code == 403
    assert [each["id"] for each in items.data] == [bread["id"]]


def test_a_bought_tag_without_a_product_becomes_a_tagged_pantry_product(
    member_client: APIClient, home: Household
) -> None:
    eggs = make_ingredient("Jajka")
    list_id = _primary_list_id(member_client, home)
    item = _add(
        member_client, list_id, {"ingredient_id": eggs.pk, "quantity": "6", "unit_code": "szt"}
    )
    body = {"items": [{"item_id": item["id"]}]}

    bought = member_client.post(f"/api/shopping/lists/{list_id}/purchase/", body, format="json")

    product = Product.objects.get(household=home)
    link = ProductIngredient.objects.get(product=product)
    stock = InventoryItem.objects.get(product=product)
    assert bought.status_code == 204
    assert (product.name, product.default_unit_code) == ("Jajka", "szt")
    assert (link.ingredient_id, link.status, link.source) == (eggs.pk, "confirmed", "manual")
    assert (stock.quantity, stock.unit_code) == (Decimal("6.000"), "szt")


def test_a_tag_of_several_products_is_bought_only_as_a_chosen_one(
    member_client: APIClient, ala: User, home: Household, flour: Product
) -> None:
    wheat = make_ingredient("Mąka pszenna")
    spelt = make_product(home, "Mąka orkiszowa", "g")
    confirm_ingredient(ala, flour, wheat)
    confirm_ingredient(ala, spelt, wheat)
    list_id = _primary_list_id(member_client, home)
    bread = _add(member_client, list_id, {"free_text": "chleb", "quantity": "1"})
    item = _add(
        member_client, list_id, {"ingredient_id": wheat.pk, "quantity": "1", "unit_code": "kg"}
    )
    url = f"/api/shopping/lists/{list_id}/purchase/"
    unchosen = {"items": [{"item_id": bread["id"]}, {"item_id": item["id"]}]}
    chosen = {"items": [{"item_id": bread["id"]}, {"item_id": item["id"], "product_id": spelt.pk}]}

    refused = member_client.post(url, unchosen, format="json")
    pending_after_refusal = ShoppingListItem.objects.filter(status="pending").count()
    bought = member_client.post(url, chosen, format="json")

    assert (refused.status_code, refused.data["code"]) == (400, "shopping_item_product_ambiguous")
    assert pending_after_refusal == 2
    assert bought.status_code == 204
    assert InventoryItem.objects.get().product_id == spelt.pk


def test_a_chosen_product_must_carry_the_items_tag(
    member_client: APIClient, home: Household, flour: Product
) -> None:
    eggs = make_ingredient("Jajka")
    list_id = _primary_list_id(member_client, home)
    item = _add(
        member_client, list_id, {"ingredient_id": eggs.pk, "quantity": "6", "unit_code": "szt"}
    )
    body = {"items": [{"item_id": item["id"], "product_id": flour.pk}]}

    response = member_client.post(f"/api/shopping/lists/{list_id}/purchase/", body, format="json")

    assert (response.status_code, response.data["code"]) == (400, "chosen_product_not_tagged")


def test_a_bought_item_is_restored_with_the_same_id(
    member_client: APIClient, home: Household, flour: Product
) -> None:
    list_id = _primary_list_id(member_client, home)
    item = _add(member_client, list_id, {"free_text": "chleb", "quantity": "1"})
    member_client.post(f"/api/shopping/items/{item['id']}/purchase/")

    restored = member_client.post(f"/api/shopping/items/{item['id']}/restore/")

    assert (restored.data["id"], restored.data["status"]) == (item["id"], "pending")


def test_recipe_shortfall_goes_to_a_list_in_one_request(
    member_client: APIClient, ala: User, home: Household, flour: Product
) -> None:
    flour_ingredient = make_ingredient("Mąka pszenna")
    eggs = make_ingredient("Jajka")
    confirm_ingredient(ala, flour, flour_ingredient)
    InventoryItem.objects.create(product=flour, unit_code="g", quantity=Decimal("100"))
    recipe = Recipe.objects.create(
        name="Naleśniki",
        servings=2,
        preparation_time_minutes=5,
        cooking_time_minutes=10,
        difficulty="easy",
        created_by=ala,
    )
    add_recipe_line(recipe, flour_ingredient, "Mąka pszenna", "300")
    add_recipe_line(recipe, eggs, "Jajka", "120")
    body = {"recipe_id": recipe.pk, "servings": 2}
    shopping_list = ShoppingList.objects.get(household=home, is_primary=True)
    url = f"/api/shopping/lists/{shopping_list.pk}/recipe-items/"

    first = member_client.post(url, body, format="json")
    second = member_client.post(url, body, format="json")

    assert first.status_code == 200
    summary = [(each["name"], each["quantity"], each["unit_code"]) for each in second.data]
    assert summary == [("Jajka", "120.000", "g"), ("Mąka", "200.000", "g")]


def test_minimum_stock_fills_the_primary_list(
    member_client: APIClient, home: Household, flour: Product
) -> None:
    InventoryItem.objects.create(
        product=flour, unit_code="g", quantity=Decimal("100"), minimum_quantity=Decimal("500")
    )
    url = f"/api/shopping/households/{home.pk}/minimum-stock/"

    member_client.post(url)
    response = member_client.post(url)

    assert [(each["name"], each["quantity"]) for each in response.data] == [("Mąka", "400.000")]


def _pending(shopping_list: ShoppingList, **subject: object) -> ShoppingListItem:
    return ShoppingListItem.objects.create(
        shopping_list=shopping_list, quantity=Decimal("1"), status="pending", **subject
    )


def test_an_ingredient_item_is_pinned_to_a_product(
    member_client: APIClient, home: Household, flour: Product
) -> None:
    shopping_list = ShoppingList.objects.get(household=home, is_primary=True)
    eggs = make_ingredient("Jajka")
    body = {"ingredient_id": eggs.pk, "quantity": "200", "unit_code": "g"}
    item = member_client.post(f"/api/shopping/lists/{shopping_list.pk}/items/", body, format="json")

    response = member_client.put(
        f"/api/shopping/items/{item.data['id']}/product/", {"product_id": flour.pk}, format="json"
    )

    assert response.status_code == 200
    assert (response.data["product_id"], response.data["ingredient_id"]) == (flour.pk, None)


def test_the_database_keeps_one_pending_row_per_product(home: Household, flour: Product) -> None:
    shopping_list = ShoppingList.objects.get(household=home, is_primary=True)
    _pending(shopping_list, product=flour, unit_code="g")

    with pytest.raises(IntegrityError), transaction.atomic():
        _pending(shopping_list, product=flour, unit_code="g")


def test_the_database_keeps_one_pending_row_per_ingredient(home: Household) -> None:
    shopping_list = ShoppingList.objects.get(household=home, is_primary=True)
    eggs: Ingredient = make_ingredient("Jajka")
    _pending(shopping_list, ingredient=eggs, unit_code="szt")

    with pytest.raises(IntegrityError), transaction.atomic():
        _pending(shopping_list, ingredient=eggs, unit_code="szt")


def test_the_database_allows_several_text_rows(home: Household) -> None:
    shopping_list = ShoppingList.objects.get(household=home, is_primary=True)

    _pending(shopping_list, free_text="chleb")
    _pending(shopping_list, free_text="chleb")

    assert shopping_list.items.count() == 2


def test_the_database_keeps_one_primary_list_per_household(home: Household) -> None:
    with pytest.raises(IntegrityError), transaction.atomic():
        ShoppingList.objects.create(household=home, name="Druga", is_primary=True)


def test_the_database_requires_a_purchase_time_exactly_for_bought_rows(home: Household) -> None:
    shopping_list = ShoppingList.objects.get(household=home, is_primary=True)

    with pytest.raises(IntegrityError), transaction.atomic():
        ShoppingListItem.objects.create(
            shopping_list=shopping_list,
            free_text="chleb",
            quantity=Decimal("1"),
            status="purchased",
        )


def test_splitting_by_promotions_requires_promotion_access(
    member_client: APIClient, home: Household
) -> None:
    list_id = _primary_list_id(member_client, home)
    _add(member_client, list_id, {"free_text": "mleko", "quantity": "1"})

    response = member_client.post(
        f"/api/shopping/lists/{list_id}/promotion-split/", {"shops": ["lidl"]}, format="json"
    )

    assert response.status_code == 403
    assert response.data["code"] == "promotions_not_allowed"


def test_a_free_text_item_is_tagged_and_bought_into_the_pantry(
    member_client: APIClient, ala: User, home: Household
) -> None:
    eggs = make_ingredient("Jajka")
    carton = make_product(home, "Jajka z wolnego wybiegu", "szt")
    confirm_ingredient(ala, carton, eggs)
    list_id = _primary_list_id(member_client, home)
    item = _add(member_client, list_id, {"free_text": "6 jajek", "quantity": "1"})
    body = {"ingredient_id": eggs.pk, "quantity": "6", "unit_code": "szt"}

    tagged = member_client.put(f"/api/shopping/items/{item['id']}/ingredient/", body, format="json")
    member_client.post(f"/api/shopping/items/{item['id']}/purchase/")

    assert tagged.status_code == 200, tagged.data
    summary = (tagged.data["ingredient_id"], tagged.data["free_text"], tagged.data["unit_code"])
    assert summary == (eggs.pk, None, "szt")
    assert InventoryItem.objects.get(product=carton).quantity == Decimal("6.000")


def test_tagging_an_item_requires_a_unit(member_client: APIClient, home: Household) -> None:
    eggs = make_ingredient("Jajka")
    list_id = _primary_list_id(member_client, home)
    item = _add(member_client, list_id, {"free_text": "jajka", "quantity": "1"})
    body = {"ingredient_id": eggs.pk, "quantity": "6"}

    response = member_client.put(
        f"/api/shopping/items/{item['id']}/ingredient/", body, format="json"
    )

    assert response.status_code == 400


InstallInterpreter = Callable[[LineInterpreter], None]


@pytest.fixture
def use_interpreter(monkeypatch: pytest.MonkeyPatch) -> Iterator[InstallInterpreter]:
    def install(interpreter: LineInterpreter) -> None:
        def build(open_interpretation: object) -> LineInterpreter:
            return interpreter

        monkeypatch.setattr("config.composition.CatalogLineInterpreter", build)
        container.cache_clear()

    yield install
    container.cache_clear()


class UnavailableLineInterpreter(LineInterpreter):
    def interpret(self, texts: tuple[str, ...], now: datetime) -> dict[str, LineMeaning]:
        raise TaggingUnavailableError


def test_the_model_proposes_a_tag_for_one_item(
    member_client: APIClient, home: Household, use_interpreter: InstallInterpreter
) -> None:
    eggs = make_ingredient("Jajka")
    meaning = LineMeaning(ingredient_id=eggs.pk, quantity=Decimal("6"), unit_code="szt")
    use_interpreter(FakeLineInterpreter({"6 jajek": meaning}))
    list_id = _primary_list_id(member_client, home)
    item = _add(member_client, list_id, {"free_text": "6 jajek", "quantity": "1"})

    response = member_client.post(f"/api/shopping/items/{item['id']}/interpretation/")

    assert response.status_code == 200
    assert response.data == {
        "ingredient_id": eggs.pk,
        "ingredient_name": "Jajka",
        "quantity": "6.000",
        "unit_code": "szt",
    }


def test_an_unavailable_model_is_reported(
    member_client: APIClient, home: Household, use_interpreter: InstallInterpreter
) -> None:
    use_interpreter(UnavailableLineInterpreter())
    list_id = _primary_list_id(member_client, home)
    item = _add(member_client, list_id, {"free_text": "jajka", "quantity": "1"})

    response = member_client.post(f"/api/shopping/items/{item['id']}/interpretation/")

    assert response.status_code == 503
    assert response.data["code"] == "tagging_unavailable"
