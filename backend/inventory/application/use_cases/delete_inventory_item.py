from inventory.application.item_membership import require_item_membership
from inventory.application.ports.inventory_repository import InventoryRepository
from shared.household_membership import HouseholdMembershipReader


class DeleteInventoryItem:
    def __init__(
        self, repository: InventoryRepository, memberships: HouseholdMembershipReader
    ) -> None:
        self._repository = repository
        self._memberships = memberships

    def execute(self, user_id: int, item_id: int) -> None:
        require_item_membership(self._repository, self._memberships, user_id, item_id)
        self._repository.delete_item(item_id)
