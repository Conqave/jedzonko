from households.application.access import HouseholdAccessPolicy
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.domain.shopping_list_summary import ShoppingListSummary


class CreateShoppingList:
    def __init__(self, repository: ShoppingListRepository, access: HouseholdAccessPolicy) -> None:
        self._repository = repository
        self._access = access

    def execute(self, user_id: int, household_id: int, name: str) -> ShoppingListSummary:
        self._access.require_membership(user_id, household_id)
        return self._repository.create_list(household_id, name)
