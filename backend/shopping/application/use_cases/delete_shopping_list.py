from shared.household_membership import HouseholdMembershipReader, require_membership
from shopping.application.errors import (
    PrimaryShoppingListCannotBeDeletedError,
    ShoppingListNotFoundError,
)
from shopping.application.ports.shopping_list_repository import ShoppingListRepository


class DeleteShoppingList:
    def __init__(
        self, repository: ShoppingListRepository, memberships: HouseholdMembershipReader
    ) -> None:
        self._repository = repository
        self._memberships = memberships

    def execute(self, user_id: int, list_id: int) -> None:
        shopping_list = self._repository.find_list(list_id)
        if shopping_list is None:
            raise ShoppingListNotFoundError
        require_membership(self._memberships, user_id, shopping_list.household_id)
        if shopping_list.is_primary:
            raise PrimaryShoppingListCannotBeDeletedError
        self._repository.delete_list(list_id)
