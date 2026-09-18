from households.application.access import HouseholdAccessPolicy
from shopping.application.errors import ShoppingListItemNotFoundError
from shopping.application.ports.shopping_list_repository import ShoppingListRepository


class DeleteShoppingListItem:
    def __init__(self, repository: ShoppingListRepository, access: HouseholdAccessPolicy) -> None:
        self._repository = repository
        self._access = access

    def execute(self, user_id: int, item_id: int) -> None:
        household_id = self._repository.find_household_id_for_item(item_id)
        if household_id is None:
            raise ShoppingListItemNotFoundError
        self._access.require_membership(user_id, household_id)
        self._repository.delete_item(item_id)
