from decimal import Decimal

from inventory.application.errors import (
    DuplicateInventoryItemError,
    MeasurementUnitNotFoundError,
    ProductNotFoundError,
)
from inventory.application.item_calories import InventoryCalorieCounter
from inventory.application.ports.inventory_repository import InventoryRepository
from inventory.application.ports.product_directory import ProductDirectory
from inventory.domain.models import InventoryItemListing
from shared.household_membership import HouseholdMembershipReader, require_membership
from shared.measurement_units import find_measurement_unit


class AddInventoryItem:
    def __init__(
        self,
        repository: InventoryRepository,
        products: ProductDirectory,
        calories: InventoryCalorieCounter,
        memberships: HouseholdMembershipReader,
    ) -> None:
        self._repository = repository
        self._products = products
        self._calories = calories
        self._memberships = memberships

    def execute(
        self,
        user_id: int,
        household_id: int,
        product_id: int,
        quantity: Decimal,
        unit_code: str,
        minimum_quantity: Decimal | None,
    ) -> InventoryItemListing:
        require_membership(self._memberships, user_id, household_id)
        if not self._products.is_household_product(household_id, product_id):
            raise ProductNotFoundError
        existing = self._repository.find_item_by_product(product_id)
        if existing is not None:
            raise DuplicateInventoryItemError
        if find_measurement_unit(unit_code) is None:
            raise MeasurementUnitNotFoundError
        item = self._repository.create_item(product_id, quantity, unit_code, minimum_quantity)
        return self._calories.count(item)
