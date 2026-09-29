from datetime import UTC, datetime
from decimal import Decimal

import pytest

from shared.household_membership import NotAHouseholdMemberError
from shopping.application.errors import (
    IngredientNotFoundError,
    InvalidShoppingItemError,
    PrimaryShoppingListCannotBeDeletedError,
    ProductNotFoundError,
    ShoppingItemAlreadyPendingError,
    ShoppingItemMergeConflictError,
    ShoppingListItemNotFoundError,
    ShoppingListNotFoundError,
)
from shopping.application.use_cases.add_missing_external_recipe_items_to_shopping_list import (
    AddMissingExternalRecipeItemsToShoppingList,
)
from shopping.application.use_cases.add_missing_recipe_items_to_shopping_list import (
    AddMissingRecipeItemsToShoppingList,
)
from shopping.application.use_cases.add_shopping_list_item import AddShoppingListItem
from shopping.application.use_cases.buy_shopping_item import BuyShoppingItem
from shopping.application.use_cases.choose_shopping_item_product import ChooseShoppingItemProduct
from shopping.application.use_cases.create_primary_shopping_list import CreatePrimaryShoppingList
from shopping.application.use_cases.delete_shopping_list import DeleteShoppingList
from shopping.application.use_cases.get_shopping_list_items import GetShoppingListItems
from shopping.application.use_cases.list_shopping_lists import ListShoppingLists
from shopping.application.use_cases.reassign_shopping_ingredient import ReassignShoppingIngredient
from shopping.application.use_cases.restore_shopping_item import RestoreShoppingItem
from shopping.application.use_cases.synchronize_minimum_stock import SynchronizeMinimumStock
from shopping.domain.errors import InvalidShoppingSubjectError
from shopping.domain.inventory_stock_level import InventoryStockLevel
from shopping.domain.missing_recipe_item import MissingRecipeItem
from shopping.domain.shopping_subject import ShoppingSubject
from shopping.tests.fakes import (
    UNITS,
    FakeCatalogDirectory,
    FakeHouseholdMembershipReader,
    FakeInventoryReader,
    FakeInventoryWriter,
    FakeRecipeRequirementReader,
    FakeShoppingListRepository,
    FakeTransactionManager,
)

NOW = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
ALA = 1
HOME = 10
OTHER_HOME = 20
FLOUR = 100
FOREIGN_PRODUCT = 200
EGGS = 300


class Shopping:
    def __init__(self) -> None:
        self.repository = FakeShoppingListRepository()
        self.memberships = FakeHouseholdMembershipReader({(ALA, HOME)})
        self.catalog = FakeCatalogDirectory({FLOUR: HOME, FOREIGN_PRODUCT: OTHER_HOME}, {EGGS})
        self.transactions = FakeTransactionManager()
        self.primary = CreatePrimaryShoppingList(self.repository).execute(HOME).id

    def add(self, subject: ShoppingSubject, quantity: str, unit_code: str | None) -> int:
        use_case = AddShoppingListItem(
            self.repository, self.catalog, self.memberships, self.transactions
        )
        return use_case.execute(ALA, self.primary, subject, Decimal(quantity), unit_code).id

    def add_missing(self, missing: list[MissingRecipeItem]) -> None:
        recipes = FakeRecipeRequirementReader(missing)
        add_missing = AddMissingRecipeItemsToShoppingList(
            self.repository, recipes, self.catalog, self.memberships, self.transactions
        )
        add_missing.execute(ALA, self.primary, 1, 4)

    def quantities(self) -> list[tuple[ShoppingSubject, Decimal, str | None]]:
        return [
            (item.subject, item.quantity, None if item.unit is None else item.unit.code)
            for item in self.repository.list_pending_items(self.primary)
        ]


@pytest.fixture
def shopping() -> Shopping:
    return Shopping()


def test_listing_only_reads_and_shows_the_primary_list(shopping: Shopping) -> None:
    lists = ListShoppingLists(shopping.repository, shopping.memberships).execute(ALA, HOME)

    assert [(each.name, each.is_primary) for each in lists] == [("Lista zakupów", True)]


def test_a_non_member_sees_no_lists(shopping: Shopping) -> None:
    with pytest.raises(NotAHouseholdMemberError):
        ListShoppingLists(shopping.repository, shopping.memberships).execute(ALA, OTHER_HOME)


def test_the_primary_list_cannot_be_deleted(shopping: Shopping) -> None:
    with pytest.raises(PrimaryShoppingListCannotBeDeletedError):
        DeleteShoppingList(shopping.repository, shopping.memberships).execute(ALA, shopping.primary)


def test_items_of_an_unknown_list_are_not_found(shopping: Shopping) -> None:
    with pytest.raises(ShoppingListNotFoundError):
        GetShoppingListItems(shopping.repository, shopping.memberships).execute(ALA, 404)


def test_an_item_is_not_about_two_things() -> None:
    with pytest.raises(InvalidShoppingSubjectError):
        ShoppingSubject(product_id=FLOUR, free_text="mąka")


def test_an_item_is_about_something() -> None:
    with pytest.raises(InvalidShoppingSubjectError):
        ShoppingSubject()


def test_free_text_is_not_blank() -> None:
    with pytest.raises(InvalidShoppingSubjectError):
        ShoppingSubject(free_text="  ")


def test_a_product_from_another_household_is_rejected(shopping: Shopping) -> None:
    with pytest.raises(ProductNotFoundError):
        shopping.add(ShoppingSubject(product_id=FOREIGN_PRODUCT), "1", "kg")


def test_an_unknown_ingredient_is_rejected(shopping: Shopping) -> None:
    with pytest.raises(IngredientNotFoundError):
        shopping.add(ShoppingSubject(ingredient_id=404), "1", "szt")


def test_products_and_ingredients_need_a_unit(shopping: Shopping) -> None:
    with pytest.raises(InvalidShoppingItemError):
        shopping.add(ShoppingSubject(ingredient_id=EGGS), "6", None)
    shopping.add(ShoppingSubject(free_text="ręczniki"), "1", None)


def test_adding_the_same_subject_again_adds_to_its_pending_item(shopping: Shopping) -> None:
    first = shopping.add(ShoppingSubject(product_id=FLOUR), "1", "kg")
    again = shopping.add(ShoppingSubject(product_id=FLOUR), "2", "kg")

    assert first == again
    assert shopping.quantities() == [(ShoppingSubject(product_id=FLOUR), Decimal("3"), "kg")]


def test_a_different_unit_for_the_same_subject_is_rejected(shopping: Shopping) -> None:
    shopping.add(ShoppingSubject(product_id=FLOUR), "1", "kg")

    with pytest.raises(InvalidShoppingItemError):
        shopping.add(ShoppingSubject(product_id=FLOUR), "500", "g")


def test_missing_recipe_items_go_to_the_list_by_what_they_are(shopping: Shopping) -> None:
    shopping.add_missing(
        [
            MissingRecipeItem("Mąka", 1, FLOUR, Decimal("200"), "g"),
            MissingRecipeItem("Jajka", EGGS, None, Decimal("3"), "szt"),
            MissingRecipeItem("szczypta soli", None, None, Decimal("1"), "g"),
        ]
    )

    assert shopping.quantities() == [
        (ShoppingSubject(product_id=FLOUR), Decimal("200"), "g"),
        (ShoppingSubject(ingredient_id=EGGS), Decimal("3"), "szt"),
        (ShoppingSubject(free_text="szczypta soli"), Decimal("1"), "g"),
    ]


def test_adding_missing_recipe_items_twice_changes_nothing(shopping: Shopping) -> None:
    missing = [MissingRecipeItem("Jajka", EGGS, None, Decimal("3"), "szt")]
    shopping.add_missing(missing)

    shopping.add_missing(missing)

    assert shopping.quantities() == [(ShoppingSubject(ingredient_id=EGGS), Decimal("3"), "szt")]


def test_missing_recipe_items_raise_a_smaller_pending_amount(shopping: Shopping) -> None:
    shopping.add(ShoppingSubject(ingredient_id=EGGS), "1", "szt")

    shopping.add_missing([MissingRecipeItem("Jajka", EGGS, None, Decimal("3"), "szt")])

    assert shopping.quantities() == [(ShoppingSubject(ingredient_id=EGGS), Decimal("3"), "szt")]


def test_external_recipe_items_go_to_the_list_with_unmeasured_ones_as_text(
    shopping: Shopping,
) -> None:
    missing = [
        MissingRecipeItem("Jajka", EGGS, None, Decimal("3"), "szt"),
        MissingRecipeItem("sól", None, None, None, None),
    ]
    use_case = AddMissingExternalRecipeItemsToShoppingList(
        shopping.repository,
        FakeRecipeRequirementReader(missing),
        shopping.catalog,
        shopping.memberships,
        shopping.transactions,
    )

    use_case.execute(ALA, shopping.primary, "omlet")
    use_case.execute(ALA, shopping.primary, "omlet")

    assert shopping.quantities() == [
        (ShoppingSubject(ingredient_id=EGGS), Decimal("3"), "szt"),
        (ShoppingSubject(free_text="sól"), Decimal("1"), None),
    ]


def test_minimum_stock_fills_the_primary_list_once(shopping: Shopping) -> None:
    level = InventoryStockLevel(FLOUR, "Mąka", Decimal("100"), Decimal("500"), UNITS["g"])
    use_case = SynchronizeMinimumStock(
        shopping.repository,
        FakeInventoryReader([level]),
        shopping.memberships,
        shopping.transactions,
    )

    use_case.execute(ALA, HOME)
    use_case.execute(ALA, HOME)

    assert shopping.quantities() == [(ShoppingSubject(product_id=FLOUR), Decimal("400"), "g")]


def test_buying_a_product_adds_it_to_the_pantry_in_one_transaction(shopping: Shopping) -> None:
    item_id = shopping.add(ShoppingSubject(product_id=FLOUR), "2", "kg")
    writer = FakeInventoryWriter()
    buy = BuyShoppingItem(shopping.repository, writer, shopping.memberships, shopping.transactions)
    opened_before = shopping.transactions.opened

    buy.execute(ALA, item_id, NOW)

    assert writer.added == [(HOME, FLOUR, Decimal("2"), "kg")]
    assert shopping.transactions.opened == opened_before + 1
    with pytest.raises(ShoppingListItemNotFoundError):
        buy.execute(ALA, item_id, NOW)


def test_buying_an_ingredient_or_text_item_leaves_the_pantry_alone(shopping: Shopping) -> None:
    eggs = shopping.add(ShoppingSubject(ingredient_id=EGGS), "6", "szt")
    towels = shopping.add(ShoppingSubject(free_text="ręczniki"), "1", None)
    writer = FakeInventoryWriter()
    buy = BuyShoppingItem(shopping.repository, writer, shopping.memberships, shopping.transactions)

    buy.execute(ALA, eggs, NOW)
    buy.execute(ALA, towels, NOW)

    assert writer.added == []


def test_a_bought_item_can_be_put_back_unless_it_is_listed_again(shopping: Shopping) -> None:
    first = shopping.add(ShoppingSubject(product_id=FLOUR), "1", "kg")
    buy = BuyShoppingItem(
        shopping.repository, FakeInventoryWriter(), shopping.memberships, shopping.transactions
    )
    restore = RestoreShoppingItem(shopping.repository, shopping.memberships, shopping.transactions)
    buy.execute(ALA, first, NOW)

    restored = restore.execute(ALA, first)
    buy.execute(ALA, first, NOW)
    shopping.add(ShoppingSubject(product_id=FLOUR), "1", "kg")

    assert restored.is_purchased is False
    with pytest.raises(ShoppingItemAlreadyPendingError):
        restore.execute(ALA, first)


def choose_product(shopping: Shopping, item_id: int, product_id: int) -> None:
    use_case = ChooseShoppingItemProduct(
        shopping.repository, shopping.catalog, shopping.memberships, shopping.transactions
    )
    use_case.execute(ALA, item_id, product_id)


def test_an_ingredient_item_becomes_a_chosen_product(shopping: Shopping) -> None:
    item_id = shopping.add(ShoppingSubject(ingredient_id=EGGS), "200", "g")

    choose_product(shopping, item_id, FLOUR)

    assert shopping.quantities() == [(ShoppingSubject(product_id=FLOUR), Decimal("200"), "g")]


def test_choosing_a_product_already_on_the_list_adds_up(shopping: Shopping) -> None:
    shopping.add(ShoppingSubject(product_id=FLOUR), "100", "g")
    item_id = shopping.add(ShoppingSubject(ingredient_id=EGGS), "200", "g")

    choose_product(shopping, item_id, FLOUR)

    assert shopping.quantities() == [(ShoppingSubject(product_id=FLOUR), Decimal("300"), "g")]


def test_choosing_a_product_in_another_unit_stops(shopping: Shopping) -> None:
    shopping.add(ShoppingSubject(product_id=FLOUR), "1", "kg")
    item_id = shopping.add(ShoppingSubject(ingredient_id=EGGS), "200", "g")

    with pytest.raises(ShoppingItemMergeConflictError):
        choose_product(shopping, item_id, FLOUR)


def test_only_an_ingredient_item_gets_a_product(shopping: Shopping) -> None:
    item_id = shopping.add(ShoppingSubject(free_text="chleb"), "1", None)

    with pytest.raises(InvalidShoppingItemError):
        choose_product(shopping, item_id, FLOUR)


def test_a_product_of_another_household_cannot_be_chosen(shopping: Shopping) -> None:
    item_id = shopping.add(ShoppingSubject(ingredient_id=EGGS), "200", "g")

    with pytest.raises(ProductNotFoundError):
        choose_product(shopping, item_id, FOREIGN_PRODUCT)


def test_merging_ingredients_moves_or_adds_up_items(shopping: Shopping) -> None:
    source_item = shopping.add(ShoppingSubject(ingredient_id=EGGS), "2", "szt")
    shopping.catalog = FakeCatalogDirectory({FLOUR: HOME}, {EGGS, 301})
    shopping.add(ShoppingSubject(ingredient_id=301), "4", "szt")

    ReassignShoppingIngredient(shopping.repository).execute(EGGS, 301)

    assert shopping.repository.find_item(source_item) is None
    assert shopping.quantities() == [(ShoppingSubject(ingredient_id=301), Decimal("6"), "szt")]


def test_merging_items_in_different_units_stops(shopping: Shopping) -> None:
    shopping.add(ShoppingSubject(ingredient_id=EGGS), "2", "szt")
    shopping.catalog = FakeCatalogDirectory({FLOUR: HOME}, {EGGS, 301})
    shopping.add(ShoppingSubject(ingredient_id=301), "500", "g")

    with pytest.raises(ShoppingItemMergeConflictError):
        ReassignShoppingIngredient(shopping.repository).execute(EGGS, 301)


def test_a_missing_ingredient_is_bought_as_the_households_only_product_of_it(
    shopping: Shopping,
) -> None:
    shopping.catalog = FakeCatalogDirectory({FLOUR: HOME}, {EGGS}, only_products={EGGS: FLOUR})

    shopping.add_missing([MissingRecipeItem("Jajka", EGGS, None, Decimal("3"), "szt")])

    assert shopping.quantities() == [(ShoppingSubject(product_id=FLOUR), Decimal("3"), "szt")]
