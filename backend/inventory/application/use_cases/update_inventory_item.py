from decimal import Decimal

from inventory.application.errors import (
    InventoryItemNotFoundError,
    MeasurementUnitNotFoundError,
)
from inventory.application.ports.inventory_repository import InventoryRepository
from inventory.domain.models import InventoryItemSnapshot
from shared.household_membership import HouseholdMembershipReader, require_membership
from shared.measurement_units import find_measurement_unit


class UpdateInventoryItem:
    def __init__(
        self, repository: InventoryRepository, memberships: HouseholdMembershipReader
    ) -> None:
        self._repository = repository
        self._memberships = memberships

    def execute(
        self, user_id: int, item_id: int, quantity: Decimal | None, unit_code: str | None
    ) -> InventoryItemSnapshot:
        item = self._repository.find_item(item_id)
        if item is None:
            raise InventoryItemNotFoundError
        require_membership(self._memberships, user_id, item.household_id)
        if unit_code is not None and find_measurement_unit(unit_code) is None:
            raise MeasurementUnitNotFoundError
        return self._repository.update_item(item_id, quantity, unit_code)
