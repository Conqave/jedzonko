from shared.household_membership import HouseholdMembershipReader, require_membership
from shared.transactions import TransactionManager
from shopping.application.errors import (
    ShoppingItemAlreadyPendingError,
    ShoppingListItemNotFoundError,
    ShoppingListNotFoundError,
)
from shopping.application.item_calories import ShoppingCalorieCounter
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.domain.shopping_item_listing import ShoppingItemListing


class RestoreShoppingItem:

    def __init__(
        self,
        repository: ShoppingListRepository,
        calories: ShoppingCalorieCounter,
        memberships: HouseholdMembershipReader,
        transactions: TransactionManager,
    ) -> None:
        self._repository = repository
        self._calories = calories
        self._memberships = memberships
        self._transactions = transactions

    def execute(self, user_id: int, item_id: int) -> ShoppingItemListing:
        item = self._repository.find_item(item_id)
        if item is None or not item.is_purchased:
            raise ShoppingListItemNotFoundError
        shopping_list = self._repository.find_list(item.list_id)
        if shopping_list is None:
            raise ShoppingListNotFoundError
        require_membership(self._memberships, user_id, shopping_list.household_id)
        with self._transactions.atomic():
            if self._repository.find_pending_item(item.list_id, item.subject) is not None:
                raise ShoppingItemAlreadyPendingError
            restored = self._repository.mark_pending(item_id)
        return self._calories.count(shopping_list.household_id, restored)
