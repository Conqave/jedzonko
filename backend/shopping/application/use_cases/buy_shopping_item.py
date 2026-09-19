from django.db import transaction

from households.application.access import HouseholdAccessPolicy
from shopping.application.errors import ShoppingListItemNotFoundError
from shopping.application.ports.inventory_writer import InventoryWriter
from shopping.application.ports.shopping_list_repository import ShoppingListRepository


class BuyShoppingItem:
    def __init__(
        self,
        repository: ShoppingListRepository,
        access: HouseholdAccessPolicy,
        inventory: InventoryWriter,
    ) -> None:
        self._repository = repository
        self._access = access
        self._inventory = inventory

    def execute(self, user_id: int, item_id: int) -> None:
        household_id = self._repository.find_household_id_for_item(item_id)
        if household_id is None:
            raise ShoppingListItemNotFoundError
        self._access.require_membership(user_id, household_id)
        item = self._repository.find_pending_item(item_id)
        if item is None:
            raise ShoppingListItemNotFoundError
        with transaction.atomic():
            self._repository.purchase_item(item_id)
            if item.product_id is not None and item.unit is not None:
                self._inventory.add_purchased_quantity(
                    household_id, item.product_id, item.quantity, item.unit
                )
