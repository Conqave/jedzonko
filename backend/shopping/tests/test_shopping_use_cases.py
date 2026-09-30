from datetime import UTC, datetime
from decimal import Decimal

import pytest

from shared.household_membership import NotAHouseholdMemberError
from shared.item_calories import SubjectNutrition, TagGap
from shared.nutrition import NutritionFacts
from shopping.application.errors import (
    ChosenProductNotTaggedError,
    IngredientNotFoundError,
    InvalidShoppingItemError,
    PrimaryShoppingListCannotBeDeletedError,
    ProductNotFoundError,
    ShoppingItemAlreadyPendingError,
    ShoppingItemMergeConflictError,
    ShoppingItemProductAmbiguousError,
    ShoppingListItemNotFoundError,
    ShoppingListNotFoundError,
)
from shopping.application.item_calories import ShoppingCalorieCounter
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
from shopping.application.use_cases.delete_shopping_list_item import DeleteShoppingListItem
from shopping.application.use_cases.delete_shopping_list_items import DeleteShoppingListItems
from shopping.application.use_cases.get_shopping_list_items import GetShoppingListItems
from shopping.application.use_cases.interpret_shopping_item import InterpretShoppingItem
from shopping.application.use_cases.list_shopping_lists import ListShoppingLists
from shopping.application.use_cases.reassign_shopping_ingredient import ReassignShoppingIngredient
from shopping.application.use_cases.restore_shopping_item import RestoreShoppingItem
from shopping.application.use_cases.synchronize_minimum_stock import SynchronizeMinimumStock
from shopping.application.use_cases.tag_shopping_item import TagShoppingItem
from shopping.application.use_cases.tag_shopping_list import TagAllShoppingLists, TagShoppingList
from shopping.domain.errors import InvalidShoppingSubjectError
from shopping.domain.inventory_stock_level import InventoryStockLevel
from shopping.domain.line_meaning import LineMeaning
from shopping.domain.missing_recipe_item import MissingRecipeItem
from shopping.domain.shopping_item_interpretation import ShoppingItemInterpretation
from shopping.domain.shopping_purchase import ShoppingPurchase
from shopping.domain.shopping_subject import ShoppingSubject
from shopping.tests.fakes import (
    UNITS,
    FakeCatalogDirectory,
    FakeHouseholdMembershipReader,
    FakeInventoryReader,
    FakeInventoryWriter,
    FakeLineInterpreter,
    FakeRecipeRequirementReader,
    FakeShoppingListRepository,
    FakeSubjectNutritionReader,
    FakeTaggedProductCreator,
    FakeTransactionManager,
)

NOW = datetime(2026, 9, 28, 12, 0, tzinfo=UTC)
ALA = 1
OLA = 2
HOME = 10
OTHER_HOME = 20
FLOUR = 100
FOREIGN_PRODUCT = 200
EGGS = 300
SPELT = 400
NEW_PRODUCT = 900


class Shopping:
    def __init__(self) -> None:
        self.repository = FakeShoppingListRepository()
        self.memberships = FakeHouseholdMembershipReader({(ALA, HOME)})
        self.catalog = FakeCatalogDirectory({FLOUR: HOME, FOREIGN_PRODUCT: OTHER_HOME}, {EGGS})
        self.transactions = FakeTransactionManager()
        self.writer = FakeInventoryWriter()
        self.products = FakeTaggedProductCreator(NEW_PRODUCT)
        self.nutrition = FakeSubjectNutritionReader()
        self.calories = ShoppingCalorieCounter(self.nutrition)
        self.primary = CreatePrimaryShoppingList(self.repository).execute(HOME).id

    def add(self, subject: ShoppingSubject, quantity: str, unit_code: str | None) -> int:
        use_case = AddShoppingListItem(
            self.repository, self.catalog, self.calories, self.memberships, self.transactions
        )
        listing = use_case.execute(ALA, self.primary, subject, Decimal(quantity), unit_code)
        return listing.item.id

    def add_missing(self, missing: list[MissingRecipeItem]) -> None:
        recipes = FakeRecipeRequirementReader(missing)
        add_missing = AddMissingRecipeItemsToShoppingList(
            self.repository,
            recipes,
            self.catalog,
            self.calories,
            self.memberships,
            self.transactions,
        )
        add_missing.execute(ALA, self.primary, 1, 4)

    def buyer(self) -> BuyShoppingItem:
        return BuyShoppingItem(
            self.repository,
            self.writer,
            self.catalog,
            self.products,
            self.memberships,
            self.transactions,
        )

    def buy(self, item_id: int, chosen_product_id: int | None) -> None:
        purchase = ShoppingPurchase(item_id=item_id, chosen_product_id=chosen_product_id)
        self.buyer().execute(ALA, purchase, NOW)

    def deleter(self) -> DeleteShoppingListItems:
        delete_item = DeleteShoppingListItem(self.repository, self.memberships)
        return DeleteShoppingListItems(self.repository, delete_item, self.transactions)

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
        GetShoppingListItems(shopping.repository, shopping.calories, shopping.memberships).execute(
            ALA, 404
        )


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
        shopping.calories,
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
        shopping.calories,
        shopping.memberships,
        shopping.transactions,
    )

    use_case.execute(ALA, HOME)
    use_case.execute(ALA, HOME)

    assert shopping.quantities() == [(ShoppingSubject(product_id=FLOUR), Decimal("400"), "g")]


def test_buying_a_product_adds_it_to_the_pantry_in_one_transaction(shopping: Shopping) -> None:
    item_id = shopping.add(ShoppingSubject(product_id=FLOUR), "2", "kg")
    opened_before = shopping.transactions.opened

    shopping.buy(item_id, None)

    assert shopping.writer.added == [(HOME, FLOUR, Decimal("2"), "kg")]
    assert shopping.transactions.opened == opened_before + 1
    with pytest.raises(ShoppingListItemNotFoundError):
        shopping.buy(item_id, None)


def test_buying_a_text_item_leaves_the_pantry_alone(shopping: Shopping) -> None:
    towels = shopping.add(ShoppingSubject(free_text="ręczniki"), "1", None)

    shopping.buy(towels, None)

    assert shopping.writer.added == []
    assert shopping.products.created == []


def test_a_tag_without_a_product_gets_one_named_after_it_and_stocked(
    shopping: Shopping,
) -> None:
    shopping.catalog = FakeCatalogDirectory({}, {EGGS}, ingredient_names={EGGS: "Jajka"})
    eggs = shopping.add(ShoppingSubject(ingredient_id=EGGS), "1", "kg")

    shopping.buy(eggs, None)

    assert shopping.products.created == [(HOME, NEW_PRODUCT, EGGS, "Jajka", "g")]
    assert shopping.writer.added == [(HOME, NEW_PRODUCT, Decimal("1"), "kg")]


def test_a_tag_with_several_products_needs_a_chosen_one(shopping: Shopping) -> None:
    shopping.catalog = FakeCatalogDirectory(
        {FLOUR: HOME, SPELT: HOME}, {EGGS}, ingredient_products={EGGS: (FLOUR, SPELT)}
    )
    eggs = shopping.add(ShoppingSubject(ingredient_id=EGGS), "6", "szt")

    with pytest.raises(ShoppingItemProductAmbiguousError):
        shopping.buy(eggs, None)
    with pytest.raises(ChosenProductNotTaggedError):
        shopping.buy(eggs, FOREIGN_PRODUCT)
    shopping.buy(eggs, SPELT)

    assert shopping.writer.added == [(HOME, SPELT, Decimal("6"), "szt")]
    assert shopping.products.created == []


def test_only_a_tagged_item_takes_a_chosen_product(shopping: Shopping) -> None:
    flour = shopping.add(ShoppingSubject(product_id=FLOUR), "1", "kg")
    towels = shopping.add(ShoppingSubject(free_text="ręczniki"), "1", None)

    with pytest.raises(InvalidShoppingItemError):
        shopping.buy(flour, FLOUR)
    with pytest.raises(InvalidShoppingItemError):
        shopping.buy(towels, FLOUR)


def test_a_bought_item_can_be_put_back_unless_it_is_listed_again(shopping: Shopping) -> None:
    first = shopping.add(ShoppingSubject(product_id=FLOUR), "1", "kg")
    restore = RestoreShoppingItem(
        shopping.repository, shopping.calories, shopping.memberships, shopping.transactions
    )
    shopping.buy(first, None)

    restored = restore.execute(ALA, first)
    shopping.buy(first, None)
    shopping.add(ShoppingSubject(product_id=FLOUR), "1", "kg")

    assert restored.item.is_purchased is False
    with pytest.raises(ShoppingItemAlreadyPendingError):
        restore.execute(ALA, first)


def test_ticked_items_are_deleted_in_one_transaction(shopping: Shopping) -> None:
    flour = shopping.add(ShoppingSubject(product_id=FLOUR), "1", "kg")
    bread = shopping.add(ShoppingSubject(free_text="chleb"), "1", None)
    towels = shopping.add(ShoppingSubject(free_text="ręczniki"), "1", None)
    opened_before = shopping.transactions.opened

    shopping.deleter().execute(ALA, shopping.primary, (flour, bread))

    assert list(shopping.repository.items) == [towels]
    assert shopping.transactions.opened == opened_before + 1


def test_deleted_items_must_belong_to_the_list(shopping: Shopping) -> None:
    bread = shopping.add(ShoppingSubject(free_text="chleb"), "1", None)
    other_list = shopping.primary + 1

    with pytest.raises(ShoppingListItemNotFoundError):
        shopping.deleter().execute(ALA, other_list, (bread,))
    with pytest.raises(ShoppingListItemNotFoundError):
        shopping.deleter().execute(ALA, shopping.primary, (bread + 1,))


def test_only_members_delete_ticked_items(shopping: Shopping) -> None:
    bread = shopping.add(ShoppingSubject(free_text="chleb"), "1", None)

    with pytest.raises(NotAHouseholdMemberError):
        shopping.deleter().execute(OLA, shopping.primary, (bread,))
    assert list(shopping.repository.items) == [bread]


def choose_product(shopping: Shopping, item_id: int, product_id: int) -> None:
    use_case = ChooseShoppingItemProduct(
        shopping.repository,
        shopping.catalog,
        shopping.calories,
        shopping.memberships,
        shopping.transactions,
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
    shopping.catalog = FakeCatalogDirectory(
        {FLOUR: HOME}, {EGGS}, ingredient_products={EGGS: (FLOUR,)}
    )

    shopping.add_missing([MissingRecipeItem("Jajka", EGGS, None, Decimal("3"), "szt")])

    assert shopping.quantities() == [(ShoppingSubject(product_id=FLOUR), Decimal("3"), "szt")]


def tag(shopping: Shopping, meanings: dict[str, LineMeaning]) -> None:
    use_case = TagShoppingList(
        shopping.repository,
        FakeLineInterpreter(meanings),
        shopping.calories,
        shopping.memberships,
        shopping.transactions,
    )
    use_case.execute(ALA, shopping.primary, NOW)


def test_free_text_items_become_tagged_ingredient_items() -> None:
    shopping = Shopping()
    shopping.add(ShoppingSubject(free_text="2 litry mleka"), "1", None)
    shopping.add(ShoppingSubject(free_text="coś na ząb"), "1", None)
    milk = LineMeaning(ingredient_id=EGGS, quantity=Decimal("2"), unit_code="l")

    tag(shopping, {"2 litry mleka": milk, "coś na ząb": LineMeaning(None, None, None)})

    assert shopping.quantities() == [
        (ShoppingSubject(ingredient_id=EGGS), Decimal("2"), "l"),
        (ShoppingSubject(free_text="coś na ząb"), Decimal("1"), None),
    ]


def test_a_tag_without_an_amount_is_counted_in_pieces() -> None:
    shopping = Shopping()
    shopping.add(ShoppingSubject(free_text="jajka"), "6", None)

    tag(shopping, {"jajka": LineMeaning(ingredient_id=EGGS, quantity=None, unit_code=None)})

    assert shopping.quantities() == [(ShoppingSubject(ingredient_id=EGGS), Decimal("6"), "szt")]


def test_a_tagged_line_adds_up_with_a_pending_item_of_the_same_tag() -> None:
    shopping = Shopping()
    shopping.add(ShoppingSubject(ingredient_id=EGGS), "4", "szt")
    shopping.add(ShoppingSubject(free_text="6 jajek"), "1", None)

    tag(
        shopping,
        {"6 jajek": LineMeaning(ingredient_id=EGGS, quantity=Decimal("6"), unit_code="szt")},
    )

    assert shopping.quantities() == [(ShoppingSubject(ingredient_id=EGGS), Decimal("10"), "szt")]


def test_every_list_with_free_text_is_tagged_in_one_run() -> None:
    shopping = Shopping()
    shopping.add(ShoppingSubject(free_text="jajka"), "6", None)
    tag_list = TagShoppingList(
        shopping.repository,
        FakeLineInterpreter(
            {"jajka": LineMeaning(ingredient_id=EGGS, quantity=None, unit_code=None)}
        ),
        shopping.calories,
        shopping.memberships,
        shopping.transactions,
    )

    count = TagAllShoppingLists(shopping.repository, tag_list).execute(NOW)

    assert count == 1
    assert shopping.quantities() == [(ShoppingSubject(ingredient_id=EGGS), Decimal("6"), "szt")]


def test_buying_an_ingredient_item_stocks_the_households_only_product_of_it(
    shopping: Shopping,
) -> None:
    shopping.catalog = FakeCatalogDirectory(
        {FLOUR: HOME}, {EGGS}, ingredient_products={EGGS: (FLOUR,)}
    )
    eggs = shopping.add(ShoppingSubject(ingredient_id=EGGS), "6", "szt")

    shopping.buy(eggs, None)

    assert shopping.writer.added == [(HOME, FLOUR, Decimal("6"), "szt")]
    assert shopping.products.created == []


def tag_item(shopping: Shopping, item_id: int, quantity: str, unit_code: str) -> None:
    use_case = TagShoppingItem(
        shopping.repository,
        shopping.catalog,
        shopping.calories,
        shopping.memberships,
        shopping.transactions,
    )
    use_case.execute(ALA, item_id, EGGS, Decimal(quantity), unit_code)


def test_a_free_text_item_is_tagged_by_hand(shopping: Shopping) -> None:
    item_id = shopping.add(ShoppingSubject(free_text="6 jajek"), "1", None)

    tag_item(shopping, item_id, "6", "szt")

    assert shopping.quantities() == [(ShoppingSubject(ingredient_id=EGGS), Decimal("6"), "szt")]


def test_a_product_item_is_retagged_by_hand(shopping: Shopping) -> None:
    item_id = shopping.add(ShoppingSubject(product_id=FLOUR), "2", "kg")

    tag_item(shopping, item_id, "10", "szt")

    assert shopping.quantities() == [(ShoppingSubject(ingredient_id=EGGS), Decimal("10"), "szt")]


def test_retagging_an_item_with_its_own_tag_changes_the_amount(shopping: Shopping) -> None:
    item_id = shopping.add(ShoppingSubject(ingredient_id=EGGS), "4", "szt")

    tag_item(shopping, item_id, "8", "szt")

    assert shopping.quantities() == [(ShoppingSubject(ingredient_id=EGGS), Decimal("8"), "szt")]


def test_a_hand_tagged_item_adds_up_with_a_pending_item_of_the_same_tag(
    shopping: Shopping,
) -> None:
    shopping.add(ShoppingSubject(ingredient_id=EGGS), "4", "szt")
    item_id = shopping.add(ShoppingSubject(free_text="jajka"), "1", None)

    tag_item(shopping, item_id, "6", "szt")

    assert shopping.quantities() == [(ShoppingSubject(ingredient_id=EGGS), Decimal("10"), "szt")]


def test_a_hand_tag_in_another_unit_than_the_pending_item_is_rejected(
    shopping: Shopping,
) -> None:
    shopping.add(ShoppingSubject(ingredient_id=EGGS), "4", "szt")
    item_id = shopping.add(ShoppingSubject(free_text="jajka"), "1", None)

    with pytest.raises(ShoppingItemMergeConflictError):
        tag_item(shopping, item_id, "300", "g")


def test_a_hand_tag_must_be_a_known_ingredient_with_a_valid_amount(shopping: Shopping) -> None:
    item_id = shopping.add(ShoppingSubject(free_text="jajka"), "1", None)
    use_case = TagShoppingItem(
        shopping.repository,
        shopping.catalog,
        shopping.calories,
        shopping.memberships,
        shopping.transactions,
    )

    with pytest.raises(IngredientNotFoundError):
        use_case.execute(ALA, item_id, FLOUR, Decimal("1"), "szt")
    with pytest.raises(InvalidShoppingItemError):
        use_case.execute(ALA, item_id, EGGS, Decimal("1"), "furlong")


def test_only_members_tag_pending_items(shopping: Shopping) -> None:
    item_id = shopping.add(ShoppingSubject(free_text="jajka"), "1", None)
    use_case = TagShoppingItem(
        shopping.repository,
        shopping.catalog,
        shopping.calories,
        shopping.memberships,
        shopping.transactions,
    )

    with pytest.raises(NotAHouseholdMemberError):
        use_case.execute(2, item_id, EGGS, Decimal("1"), "szt")


def interpret(shopping: Shopping, item_id: int, meanings: dict[str, LineMeaning]) -> object:
    use_case = InterpretShoppingItem(
        shopping.repository, FakeLineInterpreter(meanings), shopping.catalog, shopping.memberships
    )
    return use_case.execute(ALA, item_id, NOW)


def test_the_model_proposes_a_tag_and_an_amount_for_an_item() -> None:
    shopping = Shopping()
    shopping.catalog = FakeCatalogDirectory({}, {EGGS}, ingredient_names={EGGS: "Jajka"})
    item_id = shopping.add(ShoppingSubject(free_text="6 jajek"), "1", None)
    meaning = LineMeaning(ingredient_id=EGGS, quantity=Decimal("6"), unit_code="szt")

    proposal = interpret(shopping, item_id, {"6 jajek": meaning})

    assert proposal == ShoppingItemInterpretation(EGGS, "Jajka", Decimal("6"), "szt")
    assert shopping.quantities() == [(ShoppingSubject(free_text="6 jajek"), Decimal("1"), None)]


def test_an_unrecognised_item_gets_an_empty_proposal(shopping: Shopping) -> None:
    item_id = shopping.add(ShoppingSubject(free_text="coś na ząb"), "1", None)

    proposal = interpret(shopping, item_id, {})

    assert proposal == ShoppingItemInterpretation(None, None, None, None)


def test_a_proposed_tag_outside_the_catalog_is_dropped(shopping: Shopping) -> None:
    item_id = shopping.add(ShoppingSubject(free_text="6 jajek"), "1", None)
    meaning = LineMeaning(ingredient_id=EGGS, quantity=Decimal("6"), unit_code="szt")

    proposal = interpret(shopping, item_id, {"6 jajek": meaning})

    assert proposal == ShoppingItemInterpretation(None, None, Decimal("6"), "szt")


def test_listed_items_carry_calories_by_what_they_are_about(shopping: Shopping) -> None:
    flour_facts = NutritionFacts(
        kcal_per_100g=Decimal("364"), grams_per_piece=None, grams_per_ml=None
    )
    egg_facts = NutritionFacts(
        kcal_per_100g=Decimal("143"), grams_per_piece=Decimal("60"), grams_per_ml=None
    )
    shopping.nutrition = FakeSubjectNutritionReader(
        {FLOUR: SubjectNutrition(facts=flour_facts, package=None)},
        {EGGS: SubjectNutrition(facts=egg_facts, package=None)},
    )
    shopping.calories = ShoppingCalorieCounter(shopping.nutrition)
    shopping.add(ShoppingSubject(product_id=FLOUR), "1", "kg")
    shopping.add(ShoppingSubject(ingredient_id=EGGS), "10", "szt")
    shopping.add(ShoppingSubject(free_text="ręczniki"), "1", None)
    get_items = GetShoppingListItems(shopping.repository, shopping.calories, shopping.memberships)

    listings = get_items.execute(ALA, shopping.primary)

    calories = [listing.calories for listing in listings]
    assert [entry.kcal for entry in calories] == [Decimal("3640"), Decimal("858"), None]
    assert [entry.is_estimate for entry in calories] == [False, True, False]
    assert calories[2].uncounted_reason is TagGap.NO_TAG
    assert shopping.nutrition.product_lookups[-1] == (HOME, frozenset({FLOUR}))
