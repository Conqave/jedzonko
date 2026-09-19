from decimal import Decimal

from households.application.access import HouseholdAccessPolicy
from inventory.application.errors import (
    DuplicateInventoryItemError,
    InventoryCategoryNotFoundError,
)
from inventory.application.ports.inventory_category_repository import InventoryCategoryRepository
from inventory.application.ports.inventory_repository import InventoryRepository
from inventory.domain.models import InventoryItemSnapshot


class AddInventoryItem:
    def __init__(
        self,
        repository: InventoryRepository,
        categories: InventoryCategoryRepository,
        access: HouseholdAccessPolicy,
    ) -> None:
        self._repository = repository
        self._categories = categories
        self._access = access

    def execute(
        self,
        user_id: int,
        household_id: int,
        product_id: int,
        quantity: Decimal,
        unit_code: str,
        minimum_quantity: Decimal | None,
        category_id: int | None,
    ) -> InventoryItemSnapshot:
        self._access.require_membership(user_id, household_id)
        if category_id is not None:
            category_household_id = self._categories.find_household_id_for_category(category_id)
            if category_household_id != household_id:
                raise InventoryCategoryNotFoundError
        existing = self._repository.find_item_by_product(household_id, product_id)
        if existing is not None:
            raise DuplicateInventoryItemError
        return self._repository.create_item(
            household_id, product_id, quantity, unit_code, minimum_quantity, category_id
        )
