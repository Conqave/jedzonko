from dataclasses import dataclass

from shared.household_membership import HouseholdMembershipReader
from shared.transactions import TransactionManager
from shopping.application.ports.catalog_directory import CatalogDirectory
from shopping.application.ports.household_inventory_reader import HouseholdInventoryReader
from shopping.application.ports.inventory_writer import InventoryWriter
from shopping.application.ports.line_interpreter import LineInterpreter
from shopping.application.ports.promotion_coverage_reader import PromotionCoverageReader
from shopping.application.ports.recipe_requirement_reader import RecipeRequirementReader
from shopping.application.use_cases.add_missing_external_recipe_items_to_shopping_list import (
    AddMissingExternalRecipeItemsToShoppingList,
)
from shopping.application.use_cases.add_missing_recipe_items_to_shopping_list import (
    AddMissingRecipeItemsToShoppingList,
)
from shopping.application.use_cases.add_shopping_list_item import AddShoppingListItem
from shopping.application.use_cases.buy_shopping_item import BuyShoppingItem
from shopping.application.use_cases.buy_shopping_items import BuyShoppingItems
from shopping.application.use_cases.choose_shopping_item_product import ChooseShoppingItemProduct
from shopping.application.use_cases.create_primary_shopping_list import CreatePrimaryShoppingList
from shopping.application.use_cases.create_shopping_list import CreateShoppingList
from shopping.application.use_cases.delete_shopping_list import DeleteShoppingList
from shopping.application.use_cases.delete_shopping_list_item import DeleteShoppingListItem
from shopping.application.use_cases.get_shopping_list_items import GetShoppingListItems
from shopping.application.use_cases.interpret_shopping_item import InterpretShoppingItem
from shopping.application.use_cases.list_shopping_lists import ListShoppingLists
from shopping.application.use_cases.reassign_shopping_ingredient import ReassignShoppingIngredient
from shopping.application.use_cases.rename_shopping_list import RenameShoppingList
from shopping.application.use_cases.restore_shopping_item import RestoreShoppingItem
from shopping.application.use_cases.split_shopping_list_by_promotions import (
    SplitShoppingListByPromotions,
)
from shopping.application.use_cases.synchronize_minimum_stock import SynchronizeMinimumStock
from shopping.application.use_cases.tag_shopping_item import TagShoppingItem
from shopping.application.use_cases.tag_shopping_list import (
    TagAllShoppingLists,
    TagShoppingList,
)
from shopping.infrastructure.django_shopping_list_repository import DjangoShoppingListRepository


@dataclass(frozen=True, slots=True)
class ShoppingModule:
    list_shopping_lists: ListShoppingLists
    create_shopping_list: CreateShoppingList
    rename_shopping_list: RenameShoppingList
    delete_shopping_list: DeleteShoppingList
    get_shopping_list_items: GetShoppingListItems
    add_shopping_list_item: AddShoppingListItem
    add_missing_recipe_items_to_shopping_list: AddMissingRecipeItemsToShoppingList
    add_missing_external_recipe_items_to_shopping_list: AddMissingExternalRecipeItemsToShoppingList
    synchronize_minimum_stock: SynchronizeMinimumStock
    buy_shopping_item: BuyShoppingItem
    buy_shopping_items: BuyShoppingItems
    restore_shopping_item: RestoreShoppingItem
    delete_shopping_list_item: DeleteShoppingListItem
    choose_shopping_item_product: ChooseShoppingItemProduct
    tag_shopping_item: TagShoppingItem
    interpret_shopping_item: InterpretShoppingItem
    tag_shopping_list: TagShoppingList
    tag_all_shopping_lists: TagAllShoppingLists
    split_shopping_list_by_promotions: SplitShoppingListByPromotions


def build_create_primary_shopping_list() -> CreatePrimaryShoppingList:
    return CreatePrimaryShoppingList(DjangoShoppingListRepository())


def build_reassign_shopping_ingredient() -> ReassignShoppingIngredient:
    return ReassignShoppingIngredient(DjangoShoppingListRepository())


def build_shopping(
    memberships: HouseholdMembershipReader,
    catalog: CatalogDirectory,
    inventory_reader: HouseholdInventoryReader,
    inventory_writer: InventoryWriter,
    recipes: RecipeRequirementReader,
    promotions: PromotionCoverageReader,
    line_interpreter: LineInterpreter,
    transactions: TransactionManager,
) -> ShoppingModule:
    lists = DjangoShoppingListRepository()
    tag_list = TagShoppingList(lists, line_interpreter, memberships, transactions)
    buy_item = BuyShoppingItem(lists, inventory_writer, catalog, memberships, transactions)
    add_missing = AddMissingRecipeItemsToShoppingList(
        lists, recipes, catalog, memberships, transactions
    )
    return ShoppingModule(
        list_shopping_lists=ListShoppingLists(lists, memberships),
        create_shopping_list=CreateShoppingList(lists, memberships),
        rename_shopping_list=RenameShoppingList(lists, memberships),
        delete_shopping_list=DeleteShoppingList(lists, memberships),
        get_shopping_list_items=GetShoppingListItems(lists, memberships),
        add_shopping_list_item=AddShoppingListItem(lists, catalog, memberships, transactions),
        add_missing_recipe_items_to_shopping_list=add_missing,
        add_missing_external_recipe_items_to_shopping_list=(
            AddMissingExternalRecipeItemsToShoppingList(
                lists, recipes, catalog, memberships, transactions
            )
        ),
        synchronize_minimum_stock=SynchronizeMinimumStock(
            lists, inventory_reader, memberships, transactions
        ),
        buy_shopping_item=buy_item,
        buy_shopping_items=BuyShoppingItems(lists, buy_item, transactions),
        restore_shopping_item=RestoreShoppingItem(lists, memberships, transactions),
        delete_shopping_list_item=DeleteShoppingListItem(lists, memberships),
        choose_shopping_item_product=ChooseShoppingItemProduct(
            lists, catalog, memberships, transactions
        ),
        tag_shopping_item=TagShoppingItem(lists, catalog, memberships, transactions),
        interpret_shopping_item=InterpretShoppingItem(
            lists, line_interpreter, catalog, memberships
        ),
        tag_shopping_list=tag_list,
        tag_all_shopping_lists=TagAllShoppingLists(lists, tag_list),
        split_shopping_list_by_promotions=SplitShoppingListByPromotions(
            lists, promotions, memberships, transactions
        ),
    )
