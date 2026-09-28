from shared.household_membership import HouseholdMembershipReader, require_membership
from shopping.application.ports.shopping_list_repository import ShoppingListRepository
from shopping.domain.shopping_list_summary import ShoppingListSummary


class ListShoppingLists:
    def __init__(
        self, repository: ShoppingListRepository, memberships: HouseholdMembershipReader
    ) -> None:
        self._repository = repository
        self._memberships = memberships

    def execute(self, user_id: int, household_id: int) -> list[ShoppingListSummary]:
        require_membership(self._memberships, user_id, household_id)
        return self._repository.list_lists(household_id)
