from decimal import Decimal

from households.application.access import HouseholdAccessPolicy
from households.application.use_cases.rename_household_product import RenameHouseholdProduct
from inventory.application.errors import (
    InventoryItemNotFoundError,
    MeasurementUnitNotFoundError,
)
from inventory.application.ports.inventory_repository import InventoryRepository
from inventory.application.ports.transaction_manager import TransactionManager
from inventory.domain.models import InventoryItemSnapshot
from shared.measurement_units import find_measurement_unit


class UpdateInventoryItem:
    def __init__(
        self,
        repository: InventoryRepository,
        rename_product: RenameHouseholdProduct,
        transaction_manager: TransactionManager,
        access: HouseholdAccessPolicy,
    ) -> None:
        self._repository = repository
        self._rename_product = rename_product
        self._transaction_manager = transaction_manager
        self._access = access

    def execute(
        self,
        user_id: int,
        item_id: int,
        product_name: str | None,
        quantity: Decimal | None,
        unit_code: str | None,
    ) -> InventoryItemSnapshot:
        household_id = self._repository.find_household_id_for_item(item_id)
        if household_id is None:
            raise InventoryItemNotFoundError
        self._access.require_membership(user_id, household_id)
        item = self._repository.find_item(item_id)
        if item is None:
            raise InventoryItemNotFoundError
        if unit_code is not None and find_measurement_unit(unit_code) is None:
            raise MeasurementUnitNotFoundError
        with self._transaction_manager.atomic():
            if product_name is not None:
                self._rename_product.execute(user_id, household_id, item.product_id, product_name)
            return self._repository.update_item(item_id, quantity, unit_code)
