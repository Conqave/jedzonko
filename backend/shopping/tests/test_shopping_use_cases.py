from decimal import Decimal

import pytest

from households.application.access import HouseholdAccessPolicy
from households.application.errors import NotAHouseholdMemberError
from shopping.application.errors import (
    AlreadyPurchasedError,
    InvalidShoppingItemError,
    ShoppingListItemNotFoundError,
    ShoppingListNotFoundError,
)
from shopping.application.use_cases.add_missing_recipe_items_to_shopping_list import (
    AddMissingRecipeItemsToShoppingList,
)
from shopping.application.use_cases.add_shopping_list_item import AddShoppingListItem
from shopping.application.use_cases.buy_shopping_item import BuyShoppingItem
from shopping.application.use_cases.create_shopping_list import CreateShoppingList
from shopping.application.use_cases.delete_shopping_list_item import DeleteShoppingListItem
from shopping.application.use_cases.get_shopping_list_items import GetShoppingListItems
from shopping.application.use_cases.list_shopping_lists import ListShoppingLists
from shopping.application.use_cases.synchronize_minimum_stock import SynchronizeMinimumStock
from shopping.domain.inventory_stock_level import InventoryStockLevel
from shopping.domain.missing_recipe_item import MissingRecipeItem
from shopping.tests.fakes import (
    UNITS,
    FakeHouseholdInventoryReader,
    FakeHouseholdRepository,
    FakeInventoryWriter,
    FakeRecipeRequirementReader,
    FakeShoppingListRepository,
)

MEMBER_ID = 1
OUTSIDER_ID = 2
HOUSEHOLD_ID = 10


def _access() -> HouseholdAccessPolicy:
    return HouseholdAccessPolicy(FakeHouseholdRepository({(MEMBER_ID, HOUSEHOLD_ID)}))


def test_list_shopping_lists_creates_the_primary_list_lazily() -> None:
    repository = FakeShoppingListRepository()
    use_case = ListShoppingLists(repository, _access())

    summaries = use_case.execute(MEMBER_ID, HOUSEHOLD_ID)

    assert [summary.is_primary for summary in summaries] == [True]
    assert len(use_case.execute(MEMBER_ID, HOUSEHOLD_ID)) == 1


def test_list_shopping_lists_rejects_non_member() -> None:
    use_case = ListShoppingLists(FakeShoppingListRepository(), _access())

    with pytest.raises(NotAHouseholdMemberError):
        use_case.execute(OUTSIDER_ID, HOUSEHOLD_ID)


def test_create_shopping_list_rejects_non_member() -> None:
    use_case = CreateShoppingList(FakeShoppingListRepository(), _access())

    with pytest.raises(NotAHouseholdMemberError):
        use_case.execute(OUTSIDER_ID, HOUSEHOLD_ID, "Weekend")


def test_get_shopping_list_items_rejects_unknown_list() -> None:
    use_case = GetShoppingListItems(FakeShoppingListRepository(), _access())

    with pytest.raises(ShoppingListNotFoundError):
        use_case.execute(MEMBER_ID, 999)


def test_get_shopping_list_items_rejects_other_household() -> None:
    repository = FakeShoppingListRepository()
    foreign_list_id = repository.seed_list(99, "Obca", True)
    use_case = GetShoppingListItems(repository, _access())

    with pytest.raises(NotAHouseholdMemberError):
        use_case.execute(MEMBER_ID, foreign_list_id)


def test_add_item_rejects_both_ingredient_and_free_text() -> None:
    repository = FakeShoppingListRepository()
    list_id = repository.seed_list(HOUSEHOLD_ID, "Lista", True)
    use_case = AddShoppingListItem(repository, _access())

    with pytest.raises(InvalidShoppingItemError):
        use_case.execute(MEMBER_ID, list_id, 5, "Ręczniki", Decimal("1"), "szt")


def test_add_item_rejects_neither_ingredient_nor_free_text() -> None:
    repository = FakeShoppingListRepository()
    list_id = repository.seed_list(HOUSEHOLD_ID, "Lista", True)
    use_case = AddShoppingListItem(repository, _access())

    with pytest.raises(InvalidShoppingItemError):
        use_case.execute(MEMBER_ID, list_id, None, None, Decimal("1"), "szt")


def test_add_item_merges_into_existing_unpurchased_catalogue_row() -> None:
    repository = FakeShoppingListRepository()
    list_id = repository.seed_list(HOUSEHOLD_ID, "Lista", True)
    use_case = AddShoppingListItem(repository, _access())

    first = use_case.execute(MEMBER_ID, list_id, 5, None, Decimal("100"), "g")
    second = use_case.execute(MEMBER_ID, list_id, 5, None, Decimal("50"), "g")

    assert first.id == second.id
    assert second.quantity == Decimal("150")
    assert len(repository.list_items(list_id)) == 1


def test_add_free_text_item_is_accepted() -> None:
    repository = FakeShoppingListRepository()
    list_id = repository.seed_list(HOUSEHOLD_ID, "Lista", True)
    use_case = AddShoppingListItem(repository, _access())

    item = use_case.execute(MEMBER_ID, list_id, None, "Ręczniki", Decimal("2"), None)

    assert item.free_text == "Ręczniki"
    assert item.unit is None


def test_add_missing_recipe_items_is_idempotent() -> None:
    repository = FakeShoppingListRepository()
    list_id = repository.seed_list(HOUSEHOLD_ID, "Lista", True)
    recipes = FakeRecipeRequirementReader(
        [
            MissingRecipeItem(
                ingredient_id=5, ingredient_name="Mąka", amount=Decimal("300"), unit_code="g"
            )
        ]
    )
    use_case = AddMissingRecipeItemsToShoppingList(repository, _access(), recipes)

    first = use_case.execute(MEMBER_ID, list_id, 1, 4)
    second = use_case.execute(MEMBER_ID, list_id, 1, 4)

    assert len(first) == 1
    assert len(second) == 1
    assert second[0].id == first[0].id
    assert second[0].quantity == Decimal("300")


def test_add_missing_recipe_items_raises_existing_quantity() -> None:
    repository = FakeShoppingListRepository()
    list_id = repository.seed_list(HOUSEHOLD_ID, "Lista", True)
    repository.add_item(list_id, 5, None, Decimal("100"), "g")
    recipes = FakeRecipeRequirementReader(
        [
            MissingRecipeItem(
                ingredient_id=5, ingredient_name="Mąka", amount=Decimal("300"), unit_code="g"
            )
        ]
    )
    use_case = AddMissingRecipeItemsToShoppingList(repository, _access(), recipes)

    items = use_case.execute(MEMBER_ID, list_id, 1, 4)

    assert len(items) == 1
    assert items[0].quantity == Decimal("300")


def test_synchronize_minimum_stock_is_idempotent() -> None:
    repository = FakeShoppingListRepository()
    list_id = repository.seed_list(HOUSEHOLD_ID, "Lista", True)
    inventory = FakeHouseholdInventoryReader(
        [
            InventoryStockLevel(
                ingredient_id=5,
                ingredient_name="Mąka",
                quantity=Decimal("100"),
                minimum_quantity=Decimal("300"),
                unit=UNITS["g"],
            )
        ]
    )
    use_case = SynchronizeMinimumStock(repository, _access(), inventory)

    first = use_case.execute(MEMBER_ID, list_id)
    second = use_case.execute(MEMBER_ID, list_id)

    assert len(first) == 1
    assert first[0].quantity == Decimal("200")
    assert [item.id for item in second] == [item.id for item in first]
    assert second[0].quantity == Decimal("200")


def test_synchronize_minimum_stock_targets_the_primary_list() -> None:
    repository = FakeShoppingListRepository()
    primary_id = repository.seed_list(HOUSEHOLD_ID, "Lista", True)
    secondary_id = repository.seed_list(HOUSEHOLD_ID, "Weekend", False)
    inventory = FakeHouseholdInventoryReader(
        [
            InventoryStockLevel(
                ingredient_id=5,
                ingredient_name="Mąka",
                quantity=Decimal("0"),
                minimum_quantity=Decimal("300"),
                unit=UNITS["g"],
            )
        ]
    )
    use_case = SynchronizeMinimumStock(repository, _access(), inventory)

    use_case.execute(MEMBER_ID, secondary_id)

    assert len(repository.list_items(primary_id)) == 1
    assert repository.list_items(secondary_id) == []


@pytest.mark.django_db
def test_buy_shopping_item_adds_quantity_to_inventory() -> None:
    repository = FakeShoppingListRepository()
    list_id = repository.seed_list(HOUSEHOLD_ID, "Lista", True)
    item = repository.add_item(list_id, 5, None, Decimal("250"), "g")
    writer = FakeInventoryWriter()
    use_case = BuyShoppingItem(repository, _access(), writer)

    use_case.execute(MEMBER_ID, item.id)

    assert writer.added == [(HOUSEHOLD_ID, 5, Decimal("250"), "g")]
    stored = repository.find_item(item.id)
    assert stored is not None
    assert stored.is_purchased


@pytest.mark.django_db
def test_buying_twice_fails() -> None:
    repository = FakeShoppingListRepository()
    list_id = repository.seed_list(HOUSEHOLD_ID, "Lista", True)
    item = repository.add_item(list_id, 5, None, Decimal("250"), "g")
    writer = FakeInventoryWriter()
    use_case = BuyShoppingItem(repository, _access(), writer)
    use_case.execute(MEMBER_ID, item.id)

    with pytest.raises(AlreadyPurchasedError):
        use_case.execute(MEMBER_ID, item.id)

    assert len(writer.added) == 1


@pytest.mark.django_db
def test_buying_free_text_item_does_not_touch_inventory() -> None:
    repository = FakeShoppingListRepository()
    list_id = repository.seed_list(HOUSEHOLD_ID, "Lista", True)
    item = repository.add_item(list_id, None, "Ręczniki", Decimal("2"), None)
    writer = FakeInventoryWriter()
    use_case = BuyShoppingItem(repository, _access(), writer)

    use_case.execute(MEMBER_ID, item.id)

    assert writer.added == []


def test_buy_unknown_item_fails() -> None:
    use_case = BuyShoppingItem(FakeShoppingListRepository(), _access(), FakeInventoryWriter())

    with pytest.raises(ShoppingListItemNotFoundError):
        use_case.execute(MEMBER_ID, 404)


def test_delete_item_rejects_other_household() -> None:
    repository = FakeShoppingListRepository()
    foreign_list_id = repository.seed_list(99, "Obca", True)
    item = repository.add_item(foreign_list_id, 5, None, Decimal("1"), "g")
    use_case = DeleteShoppingListItem(repository, _access())

    with pytest.raises(NotAHouseholdMemberError):
        use_case.execute(MEMBER_ID, item.id)


def test_delete_item_removes_the_row() -> None:
    repository = FakeShoppingListRepository()
    list_id = repository.seed_list(HOUSEHOLD_ID, "Lista", True)
    item = repository.add_item(list_id, 5, None, Decimal("1"), "g")
    use_case = DeleteShoppingListItem(repository, _access())

    use_case.execute(MEMBER_ID, item.id)

    assert repository.list_items(list_id) == []
