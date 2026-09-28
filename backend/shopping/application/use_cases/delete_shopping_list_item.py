from shared.household_membership import HouseholdMembershipReader, require_membership
from shopping.application.errors import ShoppingListItemNotFoundError, ShoppingListNotFoundError
from shopping.application.ports.shopping_list_repository import ShoppingListRepository


class DeleteShoppingListItem:
    def __init__(
        self, repository: ShoppingListRepository, memberships: HouseholdMembershipReader
    ) -> None:
        self._repository = repository
        self._memberships = memberships

    def execute(self, user_id: int, item_id: int) -> None:
        item = self._repository.find_item(item_id)
        if item is None:
            raise ShoppingListItemNotFoundError
        shopping_list = self._repository.find_list(item.list_id)
        if shopping_list is None:
            raise ShoppingListNotFoundError
        require_membership(self._memberships, user_id, shopping_list.household_id)
        self._repository.delete_item(item_id)
