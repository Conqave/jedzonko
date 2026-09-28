from shared.household_membership import HouseholdMembershipReader, require_membership
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.domain.shopping_list_summary import ShoppingListSummary


class CreateShoppingList:
    def __init__(
        self, repository: ShoppingListRepository, memberships: HouseholdMembershipReader
    ) -> None:
        self._repository = repository
        self._memberships = memberships

    def execute(self, user_id: int, household_id: int, name: str) -> ShoppingListSummary:
        require_membership(self._memberships, user_id, household_id)
        return self._repository.create_list(household_id, name, is_primary=False)
