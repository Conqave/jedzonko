from households.composition import build_household_access_policy
from inventory.application.ports.inventory_repository import InventoryRepository
from inventory.application.ports.transaction_manager import TransactionManager
from inventory.application.use_cases.add_inventory_item import AddInventoryItem
from inventory.application.use_cases.add_quantity_to_inventory import AddQuantityToInventory
from inventory.application.use_cases.consume_inventory_quantity import ConsumeInventoryQuantity
from inventory.application.use_cases.delete_inventory_item import DeleteInventoryItem
from inventory.application.use_cases.get_household_inventory import GetHouseholdInventory
from inventory.application.use_cases.update_inventory_quantity import UpdateInventoryQuantity
from inventory.infrastructure.django_inventory_repository import DjangoInventoryRepository
from inventory.infrastructure.django_transaction_manager import DjangoTransactionManager


def build_inventory_repository() -> InventoryRepository:
    return DjangoInventoryRepository()


def build_transaction_manager() -> TransactionManager:
    return DjangoTransactionManager()


def build_get_household_inventory() -> GetHouseholdInventory:
    return GetHouseholdInventory(build_inventory_repository(), build_household_access_policy())


def build_add_inventory_item() -> AddInventoryItem:
    return AddInventoryItem(build_inventory_repository(), build_household_access_policy())


def build_update_inventory_quantity() -> UpdateInventoryQuantity:
    return UpdateInventoryQuantity(build_inventory_repository(), build_household_access_policy())


def build_delete_inventory_item() -> DeleteInventoryItem:
    return DeleteInventoryItem(build_inventory_repository(), build_household_access_policy())


def build_add_quantity_to_inventory() -> AddQuantityToInventory:
    return AddQuantityToInventory(build_inventory_repository(), build_transaction_manager())


def build_consume_inventory_quantity() -> ConsumeInventoryQuantity:
    return ConsumeInventoryQuantity(build_inventory_repository(), build_transaction_manager())
