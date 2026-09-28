from inventory.application.ports.inventory_repository import InventoryRepository
from inventory.domain.models import InventoryItemSnapshot
from shared.household_membership import HouseholdMembershipReader, require_membership


class GetHouseholdInventory:
    def __init__(
        self, repository: InventoryRepository, memberships: HouseholdMembershipReader
    ) -> None:
        self._repository = repository
        self._memberships = memberships

    def execute(self, user_id: int, household_id: int) -> list[InventoryItemSnapshot]:
        require_membership(self._memberships, user_id, household_id)
        return self._repository.list_items(household_id)
