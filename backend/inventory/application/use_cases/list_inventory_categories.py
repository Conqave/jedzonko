from inventory.application.ports.inventory_category_repository import InventoryCategoryRepository
from inventory.domain.category import InventoryCategorySnapshot
from shared.household_membership import HouseholdMembershipReader, require_membership


class ListInventoryCategories:
    def __init__(
        self, repository: InventoryCategoryRepository, memberships: HouseholdMembershipReader
    ) -> None:
        self._repository = repository
        self._memberships = memberships

    def execute(self, user_id: int, household_id: int) -> list[InventoryCategorySnapshot]:
        require_membership(self._memberships, user_id, household_id)
        return self._repository.list_categories(household_id)
