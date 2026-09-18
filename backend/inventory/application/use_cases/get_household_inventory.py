from households.application.access import HouseholdAccessPolicy
from inventory.application.ports.inventory_repository import InventoryRepository
from inventory.domain.models import InventoryItemSnapshot


class GetHouseholdInventory:
    def __init__(self, repository: InventoryRepository, access: HouseholdAccessPolicy) -> None:
        self._repository = repository
        self._access = access

    def execute(self, user_id: int, household_id: int) -> list[InventoryItemSnapshot]:
        self._access.require_membership(user_id, household_id)
        return self._repository.list_items(household_id)
