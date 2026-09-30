from dataclasses import dataclass

from inventory.application.item_calories import InventoryCalorieCounter
from inventory.application.ports.product_directory import ProductDirectory
from inventory.application.ports.product_nutrition_reader import ProductNutritionReader
from inventory.application.use_cases.add_inventory_item import AddInventoryItem
from inventory.application.use_cases.add_quantity_to_inventory import AddQuantityToInventory
from inventory.application.use_cases.consume_inventory_quantity import ConsumeInventoryQuantity
from inventory.application.use_cases.delete_inventory_item import DeleteInventoryItem
from inventory.application.use_cases.delete_inventory_item_photo import DeleteInventoryItemPhoto
from inventory.application.use_cases.get_household_inventory import GetHouseholdInventory
from inventory.application.use_cases.list_inventory_listings import ListInventoryListings
from inventory.application.use_cases.set_inventory_item_minimum import SetInventoryItemMinimum
from inventory.application.use_cases.set_inventory_item_photo import SetInventoryItemPhoto
from inventory.application.use_cases.update_inventory_item import UpdateInventoryItem
from inventory.infrastructure.django_inventory_repository import DjangoInventoryRepository
from shared.household_membership import HouseholdMembershipReader
from shared.transactions import TransactionManager


@dataclass(frozen=True, slots=True)
class InventoryModule:
    get_household_inventory: GetHouseholdInventory
    list_inventory_listings: ListInventoryListings
    add_inventory_item: AddInventoryItem
    update_inventory_item: UpdateInventoryItem
    delete_inventory_item: DeleteInventoryItem
    set_inventory_item_minimum: SetInventoryItemMinimum
    set_inventory_item_photo: SetInventoryItemPhoto
    delete_inventory_item_photo: DeleteInventoryItemPhoto
    add_quantity_to_inventory: AddQuantityToInventory
    consume_inventory_quantity: ConsumeInventoryQuantity


def build_inventory(
    memberships: HouseholdMembershipReader,
    products: ProductDirectory,
    nutrition: ProductNutritionReader,
    transactions: TransactionManager,
) -> InventoryModule:
    items = DjangoInventoryRepository()
    calories = InventoryCalorieCounter(nutrition)
    return InventoryModule(
        get_household_inventory=GetHouseholdInventory(items, memberships),
        list_inventory_listings=ListInventoryListings(items, calories, memberships),
        add_inventory_item=AddInventoryItem(items, products, calories, memberships),
        update_inventory_item=UpdateInventoryItem(items, calories, memberships),
        delete_inventory_item=DeleteInventoryItem(items, memberships),
        set_inventory_item_minimum=SetInventoryItemMinimum(items, calories, memberships),
        set_inventory_item_photo=SetInventoryItemPhoto(items, calories, memberships),
        delete_inventory_item_photo=DeleteInventoryItemPhoto(items, calories, memberships),
        add_quantity_to_inventory=AddQuantityToInventory(items, products, transactions),
        consume_inventory_quantity=ConsumeInventoryQuantity(items, products, transactions),
    )
