from decimal import Decimal

from inventory.application.errors import (
    DuplicateInventoryItemError,
    InventoryCategoryNotFoundError,
    ProductNotFoundError,
)
from inventory.application.ports.inventory_category_repository import InventoryCategoryRepository
from inventory.application.ports.inventory_repository import InventoryRepository
from inventory.application.ports.product_directory import ProductDirectory
from inventory.domain.models import InventoryItemSnapshot
from shared.household_membership import HouseholdMembershipReader, require_membership


class AddInventoryItem:
    def __init__(
        self,
        repository: InventoryRepository,
        categories: InventoryCategoryRepository,
        products: ProductDirectory,
        memberships: HouseholdMembershipReader,
    ) -> None:
        self._repository = repository
        self._categories = categories
        self._products = products
        self._memberships = memberships

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
        require_membership(self._memberships, user_id, household_id)
        if not self._products.is_household_product(household_id, product_id):
            raise ProductNotFoundError
        if category_id is not None:
            category_household_id = self._categories.find_household_id_for_category(category_id)
            if category_household_id != household_id:
                raise InventoryCategoryNotFoundError
        existing = self._repository.find_item_by_product(product_id)
        if existing is not None:
            raise DuplicateInventoryItemError
        return self._repository.create_item(
            product_id, quantity, unit_code, minimum_quantity, category_id
        )
