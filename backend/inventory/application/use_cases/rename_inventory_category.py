from inventory.application.errors import InventoryCategoryNotFoundError
from inventory.application.ports.inventory_category_repository import InventoryCategoryRepository
from inventory.domain.category import InventoryCategorySnapshot
from shared.household_membership import HouseholdMembershipReader, require_membership


class RenameInventoryCategory:
    def __init__(
        self, repository: InventoryCategoryRepository, memberships: HouseholdMembershipReader
    ) -> None:
        self._repository = repository
        self._memberships = memberships

    def execute(self, user_id: int, category_id: int, name: str) -> InventoryCategorySnapshot:
        household_id = self._repository.find_household_id_for_category(category_id)
        if household_id is None:
            raise InventoryCategoryNotFoundError
        require_membership(self._memberships, user_id, household_id)
        return self._repository.rename_category(category_id, name)
