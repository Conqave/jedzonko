from datetime import datetime

from shared.household_membership import HouseholdMembershipReader, require_membership
from shared.transactions import TransactionManager
from shopping.application.errors import ShoppingListItemNotFoundError, ShoppingListNotFoundError
from shopping.application.ports.inventory_writer import InventoryWriter
from shopping.application.ports.shopping_list_repository import ShoppingListRepository


class BuyShoppingItem:

    def __init__(
        self,
        repository: ShoppingListRepository,
        inventory: InventoryWriter,
        memberships: HouseholdMembershipReader,
        transactions: TransactionManager,
    ) -> None:
        self._repository = repository
        self._inventory = inventory
        self._memberships = memberships
        self._transactions = transactions

    def execute(self, user_id: int, item_id: int, now: datetime) -> None:
        item = self._repository.find_item(item_id)
        if item is None or item.is_purchased:
            raise ShoppingListItemNotFoundError
        shopping_list = self._repository.find_list(item.list_id)
        if shopping_list is None:
            raise ShoppingListNotFoundError
        require_membership(self._memberships, user_id, shopping_list.household_id)
        with self._transactions.atomic():
            self._repository.mark_purchased(item_id, now)
            product_id = item.subject.product_id
            if product_id is not None and item.unit is not None:
                self._inventory.add_purchased_quantity(
                    shopping_list.household_id, product_id, item.quantity, item.unit
                )
