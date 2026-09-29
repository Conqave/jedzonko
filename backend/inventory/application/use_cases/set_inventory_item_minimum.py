from decimal import Decimal

from inventory.application.errors import InventoryItemNotFoundError
from inventory.application.ports.inventory_repository import InventoryRepository
from inventory.domain.models import InventoryItemSnapshot
from shared.household_membership import HouseholdMembershipReader, require_membership


class SetInventoryItemMinimum:
    def __init__(
        self, repository: InventoryRepository, memberships: HouseholdMembershipReader
    ) -> None:
        self._repository = repository
        self._memberships = memberships

    def execute(
        self, user_id: int, item_id: int, minimum_quantity: Decimal | None
    ) -> InventoryItemSnapshot:
        household_id = self._repository.find_household_id_for_item(item_id)
        if household_id is None:
            raise InventoryItemNotFoundError
        require_membership(self._memberships, user_id, household_id)
        return self._repository.set_minimum_quantity(item_id, minimum_quantity)
