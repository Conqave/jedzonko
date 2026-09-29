from dataclasses import dataclass

from inventory.application.ports.product_directory import ProductDirectory
from inventory.application.ports.product_renamer import ProductRenamer
from inventory.application.use_cases.add_inventory_item import AddInventoryItem
from inventory.application.use_cases.add_quantity_to_inventory import AddQuantityToInventory
from inventory.application.use_cases.consume_inventory_quantity import ConsumeInventoryQuantity
from inventory.application.use_cases.create_inventory_category import CreateInventoryCategory
from inventory.application.use_cases.delete_inventory_category import DeleteInventoryCategory
from inventory.application.use_cases.delete_inventory_item import DeleteInventoryItem
from inventory.application.use_cases.delete_inventory_item_photo import DeleteInventoryItemPhoto
from inventory.application.use_cases.get_household_inventory import GetHouseholdInventory
from inventory.application.use_cases.list_inventory_categories import ListInventoryCategories
from inventory.application.use_cases.rename_inventory_category import RenameInventoryCategory
from inventory.application.use_cases.set_inventory_item_category import SetInventoryItemCategory
from inventory.application.use_cases.set_inventory_item_minimum import SetInventoryItemMinimum
from inventory.application.use_cases.set_inventory_item_photo import SetInventoryItemPhoto
from inventory.application.use_cases.update_inventory_item import UpdateInventoryItem
from inventory.infrastructure.django_inventory_category_repository import (
    DjangoInventoryCategoryRepository,
)
from inventory.infrastructure.django_inventory_repository import DjangoInventoryRepository
from shared.household_membership import HouseholdMembershipReader
from shared.transactions import TransactionManager


@dataclass(frozen=True, slots=True)
class InventoryModule:
    get_household_inventory: GetHouseholdInventory
    add_inventory_item: AddInventoryItem
    update_inventory_item: UpdateInventoryItem
    delete_inventory_item: DeleteInventoryItem
    list_inventory_categories: ListInventoryCategories
    create_inventory_category: CreateInventoryCategory
    rename_inventory_category: RenameInventoryCategory
    delete_inventory_category: DeleteInventoryCategory
    set_inventory_item_minimum: SetInventoryItemMinimum
    set_inventory_item_category: SetInventoryItemCategory
    set_inventory_item_photo: SetInventoryItemPhoto
    delete_inventory_item_photo: DeleteInventoryItemPhoto
    add_quantity_to_inventory: AddQuantityToInventory
    consume_inventory_quantity: ConsumeInventoryQuantity


def build_inventory(
    memberships: HouseholdMembershipReader,
    products: ProductDirectory,
    product_renamer: ProductRenamer,
    transactions: TransactionManager,
) -> InventoryModule:
    items = DjangoInventoryRepository()
    categories = DjangoInventoryCategoryRepository()
    return InventoryModule(
        get_household_inventory=GetHouseholdInventory(items, memberships),
        add_inventory_item=AddInventoryItem(items, categories, products, memberships),
        update_inventory_item=UpdateInventoryItem(
            items, product_renamer, transactions, memberships
        ),
        delete_inventory_item=DeleteInventoryItem(items, memberships),
        list_inventory_categories=ListInventoryCategories(categories, memberships),
        create_inventory_category=CreateInventoryCategory(categories, memberships),
        rename_inventory_category=RenameInventoryCategory(categories, memberships),
        delete_inventory_category=DeleteInventoryCategory(categories, memberships),
        set_inventory_item_minimum=SetInventoryItemMinimum(items, memberships),
        set_inventory_item_category=SetInventoryItemCategory(items, categories, memberships),
        set_inventory_item_photo=SetInventoryItemPhoto(items, memberships),
        delete_inventory_item_photo=DeleteInventoryItemPhoto(items, memberships),
        add_quantity_to_inventory=AddQuantityToInventory(items, products, transactions),
        consume_inventory_quantity=ConsumeInventoryQuantity(items, products, transactions),
    )
