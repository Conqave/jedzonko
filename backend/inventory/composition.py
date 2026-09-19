from households.composition import build_household_access_policy, build_rename_household_product
from inventory.application.ports.inventory_category_repository import InventoryCategoryRepository
from inventory.application.ports.inventory_repository import InventoryRepository
from inventory.application.ports.transaction_manager import TransactionManager
from inventory.application.use_cases.add_inventory_item import AddInventoryItem
from inventory.application.use_cases.add_quantity_to_inventory import AddQuantityToInventory
from inventory.application.use_cases.consume_inventory_quantity import ConsumeInventoryQuantity
from inventory.application.use_cases.create_inventory_category import CreateInventoryCategory
from inventory.application.use_cases.delete_inventory_item import DeleteInventoryItem
from inventory.application.use_cases.delete_inventory_item_photo import DeleteInventoryItemPhoto
from inventory.application.use_cases.get_household_inventory import GetHouseholdInventory
from inventory.application.use_cases.list_inventory_categories import ListInventoryCategories
from inventory.application.use_cases.set_inventory_item_category import SetInventoryItemCategory
from inventory.application.use_cases.set_inventory_item_photo import SetInventoryItemPhoto
from inventory.application.use_cases.update_inventory_item import UpdateInventoryItem
from inventory.infrastructure.django_inventory_category_repository import (
    DjangoInventoryCategoryRepository,
)
from inventory.infrastructure.django_inventory_repository import DjangoInventoryRepository
from inventory.infrastructure.django_transaction_manager import DjangoTransactionManager


def build_inventory_repository() -> InventoryRepository:
    return DjangoInventoryRepository()


def build_inventory_category_repository() -> InventoryCategoryRepository:
    return DjangoInventoryCategoryRepository()


def build_transaction_manager() -> TransactionManager:
    return DjangoTransactionManager()


def build_get_household_inventory() -> GetHouseholdInventory:
    return GetHouseholdInventory(build_inventory_repository(), build_household_access_policy())


def build_add_inventory_item() -> AddInventoryItem:
    return AddInventoryItem(
        build_inventory_repository(),
        build_inventory_category_repository(),
        build_household_access_policy(),
    )


def build_list_inventory_categories() -> ListInventoryCategories:
    return ListInventoryCategories(
        build_inventory_category_repository(), build_household_access_policy()
    )


def build_create_inventory_category() -> CreateInventoryCategory:
    return CreateInventoryCategory(
        build_inventory_category_repository(), build_household_access_policy()
    )


def build_set_inventory_item_category() -> SetInventoryItemCategory:
    return SetInventoryItemCategory(
        build_inventory_repository(),
        build_inventory_category_repository(),
        build_household_access_policy(),
    )


def build_set_inventory_item_photo() -> SetInventoryItemPhoto:
    return SetInventoryItemPhoto(build_inventory_repository(), build_household_access_policy())


def build_delete_inventory_item_photo() -> DeleteInventoryItemPhoto:
    return DeleteInventoryItemPhoto(build_inventory_repository(), build_household_access_policy())


def build_update_inventory_item() -> UpdateInventoryItem:
    return UpdateInventoryItem(
        build_inventory_repository(),
        build_rename_household_product(),
        build_transaction_manager(),
        build_household_access_policy(),
    )


def build_delete_inventory_item() -> DeleteInventoryItem:
    return DeleteInventoryItem(build_inventory_repository(), build_household_access_policy())


def build_add_quantity_to_inventory() -> AddQuantityToInventory:
    return AddQuantityToInventory(build_inventory_repository(), build_transaction_manager())


def build_consume_inventory_quantity() -> ConsumeInventoryQuantity:
    return ConsumeInventoryQuantity(build_inventory_repository(), build_transaction_manager())
