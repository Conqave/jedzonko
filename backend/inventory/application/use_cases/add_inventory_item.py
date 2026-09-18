from decimal import Decimal

from households.application.access import HouseholdAccessPolicy
from inventory.application.errors import DuplicateInventoryItemError
from inventory.application.ports.inventory_repository import InventoryRepository
from inventory.domain.models import InventoryItemSnapshot


class AddInventoryItem:
    def __init__(self, repository: InventoryRepository, access: HouseholdAccessPolicy) -> None:
        self._repository = repository
        self._access = access

    def execute(
        self,
        user_id: int,
        household_id: int,
        ingredient_id: int,
        quantity: Decimal,
        unit_code: str,
        minimum_quantity: Decimal | None,
        category_id: int | None,
    ) -> InventoryItemSnapshot:
        self._access.require_membership(user_id, household_id)
        existing = self._repository.find_item_by_ingredient(household_id, ingredient_id)
        if existing is not None:
            raise DuplicateInventoryItemError
        return self._repository.create_item(
            household_id, ingredient_id, quantity, unit_code, minimum_quantity, category_id
        )
