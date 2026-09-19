from households.application.access import HouseholdAccessPolicy
from inventory.application.errors import (
    InventoryCategoryNotFoundError,
    InventoryItemNotFoundError,
)
from inventory.application.ports.inventory_category_repository import InventoryCategoryRepository
from inventory.application.ports.inventory_repository import InventoryRepository
from inventory.domain.models import InventoryItemSnapshot


class SetInventoryItemCategory:
    def __init__(
        self,
        repository: InventoryRepository,
        categories: InventoryCategoryRepository,
        access: HouseholdAccessPolicy,
    ) -> None:
        self._repository = repository
        self._categories = categories
        self._access = access

    def execute(self, user_id: int, item_id: int, category_id: int | None) -> InventoryItemSnapshot:
        household_id = self._repository.find_household_id_for_item(item_id)
        if household_id is None:
            raise InventoryItemNotFoundError
        self._access.require_membership(user_id, household_id)
        if category_id is not None:
            category_household_id = self._categories.find_household_id_for_category(category_id)
            if category_household_id != household_id:
                raise InventoryCategoryNotFoundError
        return self._repository.set_category(item_id, category_id)
