from decimal import Decimal

from households.application.access import HouseholdAccessPolicy
from inventory.application.errors import InventoryItemNotFoundError
from inventory.application.ports.inventory_repository import InventoryRepository
from inventory.domain.models import InventoryItemSnapshot


class UpdateInventoryQuantity:
    def __init__(self, repository: InventoryRepository, access: HouseholdAccessPolicy) -> None:
        self._repository = repository
        self._access = access

    def execute(self, user_id: int, item_id: int, quantity: Decimal) -> InventoryItemSnapshot:
        household_id = self._repository.find_household_id_for_item(item_id)
        if household_id is None:
            raise InventoryItemNotFoundError
        self._access.require_membership(user_id, household_id)
        return self._repository.set_quantity(item_id, quantity)
