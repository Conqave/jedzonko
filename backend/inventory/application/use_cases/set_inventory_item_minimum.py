from decimal import Decimal

from inventory.application.item_membership import require_item_membership
from inventory.application.ports.inventory_repository import InventoryRepository
from inventory.domain.models import InventoryItemSnapshot
from shared.household_membership import HouseholdMembershipReader


class SetInventoryItemMinimum:
    def __init__(
        self, repository: InventoryRepository, memberships: HouseholdMembershipReader
    ) -> None:
        self._repository = repository
        self._memberships = memberships

    def execute(
        self, user_id: int, item_id: int, minimum_quantity: Decimal | None
    ) -> InventoryItemSnapshot:
        require_item_membership(self._repository, self._memberships, user_id, item_id)
        return self._repository.set_minimum_quantity(item_id, minimum_quantity)
