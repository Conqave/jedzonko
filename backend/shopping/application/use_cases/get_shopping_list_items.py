from households.application.access import HouseholdAccessPolicy
from shopping.application.errors import ShoppingListNotFoundError
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.domain.shopping_item_snapshot import ShoppingItemSnapshot


class GetShoppingListItems:
    def __init__(self, repository: ShoppingListRepository, access: HouseholdAccessPolicy) -> None:
        self._repository = repository
        self._access = access

    def execute(self, user_id: int, list_id: int) -> list[ShoppingItemSnapshot]:
        household_id = self._repository.find_household_id_for_list(list_id)
        if household_id is None:
            raise ShoppingListNotFoundError
        self._access.require_membership(user_id, household_id)
        return self._repository.list_items(list_id)
