from inventory.application.ports.inventory_category_repository import InventoryCategoryRepository
from inventory.domain.category import InventoryCategorySnapshot
from shared.household_membership import HouseholdMembershipReader, require_membership


class CreateInventoryCategory:
    def __init__(
        self, repository: InventoryCategoryRepository, memberships: HouseholdMembershipReader
    ) -> None:
        self._repository = repository
        self._memberships = memberships

    def execute(self, user_id: int, household_id: int, name: str) -> InventoryCategorySnapshot:
        require_membership(self._memberships, user_id, household_id)
        return self._repository.create_category(household_id, name)
