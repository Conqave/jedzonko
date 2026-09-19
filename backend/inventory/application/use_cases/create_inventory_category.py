from households.application.access import HouseholdAccessPolicy
from inventory.application.ports.inventory_category_repository import InventoryCategoryRepository
from inventory.domain.category import InventoryCategorySnapshot


class CreateInventoryCategory:
    def __init__(
        self, repository: InventoryCategoryRepository, access: HouseholdAccessPolicy
    ) -> None:
        self._repository = repository
        self._access = access

    def execute(self, user_id: int, household_id: int, name: str) -> InventoryCategorySnapshot:
        self._access.require_membership(user_id, household_id)
        return self._repository.create_category(household_id, name)
