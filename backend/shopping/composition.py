from households.composition import build_household_access_policy
from shopping.application.ports.household_inventory_reader import HouseholdInventoryReader
from shopping.application.ports.inventory_writer import InventoryWriter
from shopping.application.ports.recipe_requirement_reader import RecipeRequirementReader
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
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
from shopping.infrastructure.django_shopping_list_repository import DjangoShoppingListRepository
from shopping.infrastructure.inventory_stock_gateway import InventoryStockGateway
from shopping.infrastructure.inventory_writer_gateway import InventoryWriterGateway
from shopping.infrastructure.recipe_requirement_gateway import RecipeRequirementGateway


def build_shopping_list_repository() -> ShoppingListRepository:
    return DjangoShoppingListRepository()


def build_household_inventory_reader() -> HouseholdInventoryReader:
    return InventoryStockGateway()


def build_inventory_writer() -> InventoryWriter:
    return InventoryWriterGateway()


def build_recipe_requirement_reader() -> RecipeRequirementReader:
    return RecipeRequirementGateway()


def build_list_shopping_lists() -> ListShoppingLists:
    return ListShoppingLists(build_shopping_list_repository(), build_household_access_policy())


def build_create_shopping_list() -> CreateShoppingList:
    return CreateShoppingList(build_shopping_list_repository(), build_household_access_policy())


def build_get_shopping_list_items() -> GetShoppingListItems:
    return GetShoppingListItems(build_shopping_list_repository(), build_household_access_policy())


def build_add_shopping_list_item() -> AddShoppingListItem:
    return AddShoppingListItem(build_shopping_list_repository(), build_household_access_policy())


def build_add_missing_recipe_items_to_shopping_list() -> AddMissingRecipeItemsToShoppingList:
    return AddMissingRecipeItemsToShoppingList(
        build_shopping_list_repository(),
        build_household_access_policy(),
        build_recipe_requirement_reader(),
    )


def build_synchronize_minimum_stock() -> SynchronizeMinimumStock:
    return SynchronizeMinimumStock(
        build_shopping_list_repository(),
        build_household_access_policy(),
        build_household_inventory_reader(),
    )


def build_buy_shopping_item() -> BuyShoppingItem:
    return BuyShoppingItem(
        build_shopping_list_repository(),
        build_household_access_policy(),
        build_inventory_writer(),
    )


def build_delete_shopping_list_item() -> DeleteShoppingListItem:
    return DeleteShoppingListItem(build_shopping_list_repository(), build_household_access_policy())
